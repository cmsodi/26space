"""
WorkflowRunner — manages orchestrator/recipe execution in a background thread.

Installs monkey-patches before the workflow starts, captures stdout,
and cleans up after completion (success or failure).
"""

import sys
import threading
import traceback
from typing import Optional

from .bridge import InteractionBridge, TeeStdout
from .patches import install_patches, uninstall_patches


class WorkflowRunner:
    """Manages running orchestrator/recipe in a background thread."""

    def __init__(self, bridge: InteractionBridge):
        self.bridge = bridge
        self._thread: Optional[threading.Thread] = None
        self._original_stdout = None
        self._step_sync_stop = threading.Event()

    @property
    def is_running(self) -> bool:
        return self.bridge.is_running.is_set()

    def start_run(self, problem: str, parallel: bool = True,
                  auto_save: bool = True, verbose: bool = True):
        """Launch a new analysis run."""
        self._start_thread(
            target=self._run_workflow,
            args=(problem, parallel, auto_save, verbose),
        )

    def start_resume(self, state_file: str, parallel: bool = True,
                     verbose: bool = True):
        """Resume from checkpoint."""
        self._start_thread(
            target=self._resume_workflow,
            args=(state_file, parallel, verbose),
        )

    def start_from_folder(self, folder_path: str, parallel: bool = True,
                          verbose: bool = True):
        """Resume from output folder (reuse analyst reports)."""
        self._start_thread(
            target=self._from_folder_workflow,
            args=(folder_path, parallel, verbose),
        )

    def start_recipe(self, recipe_name: str, topic: str,
                     context_yaml: str = None, verbose: bool = True):
        """Run a recipe."""
        self._start_thread(
            target=self._recipe_workflow,
            args=(recipe_name, topic, context_yaml, verbose),
        )

    def _start_thread(self, target, args):
        if self._thread and self._thread.is_alive():
            raise RuntimeError("A workflow is already running")

        self.bridge.reset()
        self.bridge.is_running.set()

        # Install patches and stdout capture
        install_patches(self.bridge)
        self._original_stdout = sys.stdout
        sys.stdout = TeeStdout(self.bridge.log_queue, self._original_stdout)

        self._thread = threading.Thread(target=target, args=args, daemon=True)
        self._thread.start()

    def _cleanup(self):
        """Restore original state after workflow completes."""
        self._step_sync_stop.set()
        if not self.bridge.error:
            self.bridge.current_step = "complete"
        if self._original_stdout:
            sys.stdout = self._original_stdout
            self._original_stdout = None
        uninstall_patches()
        self.bridge.is_running.clear()
        self.bridge.is_complete.set()

    def _sync_step(self, state_holder):
        """Poll orchestrator state and sync current_step to bridge.

        Args:
            state_holder: object with a .state.current_step attribute
                          (StrategicOrchestrator or similar)
        """
        self._step_sync_stop.clear()
        while not self._step_sync_stop.is_set():
            try:
                step = state_holder.state.current_step
                value = step.value if hasattr(step, 'value') else str(step)
                self.bridge.current_step = value
            except Exception:
                pass
            self._step_sync_stop.wait(0.5)

    def _run_workflow(self, problem, parallel, auto_save, verbose):
        try:
            from src.orchestrator import StrategicOrchestrator
            orch = StrategicOrchestrator(
                parallel_analysts=parallel,
                auto_save=auto_save,
                verbose=verbose,
            )
            sync = threading.Thread(target=self._sync_step, args=(orch,), daemon=True)
            sync.start()
            result = orch.run(problem)
            if result:
                doc_path = orch._save_final_document(result)
                print(f"\nFinal document saved to: {doc_path}")
                self.bridge.workflow_result = str(doc_path)
        except KeyboardInterrupt:
            print("\nWorkflow interrupted by user")
        except Exception as e:
            self.bridge.error = e
            traceback.print_exc()
        finally:
            self._cleanup()

    def _resume_workflow(self, state_file, parallel, verbose):
        try:
            from src.orchestrator import StrategicOrchestrator
            orch = StrategicOrchestrator.load_state(
                state_file,
                parallel_analysts=parallel,
                verbose=verbose,
            )
            sync = threading.Thread(target=self._sync_step, args=(orch,), daemon=True)
            sync.start()
            result = orch.resume()
            if result:
                doc_path = orch._save_final_document(result)
                print(f"\nFinal document saved to: {doc_path}")
                self.bridge.workflow_result = str(doc_path)
        except Exception as e:
            self.bridge.error = e
            traceback.print_exc()
        finally:
            self._cleanup()

    def _from_folder_workflow(self, folder_path, parallel, verbose):
        try:
            from src.orchestrator import StrategicOrchestrator
            orch = StrategicOrchestrator.load_from_folder(
                folder_path,
                parallel_analysts=parallel,
                verbose=verbose,
            )
            sync = threading.Thread(target=self._sync_step, args=(orch,), daemon=True)
            sync.start()
            result = orch.resume()
            if result:
                doc_path = orch._save_final_document(result)
                print(f"\nFinal document saved to: {doc_path}")
                self.bridge.workflow_result = str(doc_path)
        except Exception as e:
            self.bridge.error = e
            traceback.print_exc()
        finally:
            self._cleanup()

    def _recipe_workflow(self, recipe_name, topic, context_yaml, verbose):
        try:
            from src.recipe import RecipeRunner
            runner = RecipeRunner(
                recipe_name=recipe_name,
                verbose=verbose,
                context_yaml=context_yaml,
            )
            result = runner.run(topic)
            if result:
                print(f"\nDocument saved to: output/{runner.slug}/")
                self.bridge.workflow_result = f"output/{runner.slug}/"
        except Exception as e:
            self.bridge.error = e
            traceback.print_exc()
        finally:
            self._cleanup()
