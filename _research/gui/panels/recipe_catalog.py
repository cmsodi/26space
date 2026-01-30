"""
Recipe catalog — browse available recipes with descriptions and metadata.
"""

from nicegui import ui


def create_recipe_catalog():
    """Create the recipe catalog panel."""

    ui.label('Recipe Catalog').classes('text-h5 q-mb-md')
    ui.label(
        'Self-contained analytical pipelines that fuse methodology, '
        'synthesis, and output format into reusable packages.'
    ).classes('text-subtitle2 text-grey q-mb-md')

    try:
        from src.recipe import discover_recipes, load_recipe
        recipe_names = discover_recipes()
    except Exception as e:
        ui.label(f'Failed to load recipes: {e}').classes('text-negative')
        return

    if not recipe_names:
        ui.label('No recipes found in .claude/recipes/').classes('text-grey')
        return

    with ui.row().classes('w-full q-gutter-md flex-wrap'):
        for name in recipe_names:
            try:
                recipe = load_recipe(name)
                _render_recipe_card(name, recipe)
            except Exception as e:
                with ui.card().classes('q-pa-md'):
                    ui.label(name).classes('text-subtitle1 text-bold')
                    ui.label(f'Error loading: {e}').classes(
                        'text-caption text-negative'
                    )


def _render_recipe_card(name: str, recipe):
    """Render a card for a single recipe."""
    with ui.card().classes('q-pa-md').style('min-width: 300px; max-width: 400px;'):
        with ui.row().classes('items-center q-gutter-sm'):
            ui.icon('menu_book', color='primary', size='md')
            ui.label(name).classes('text-subtitle1 text-bold')

        if hasattr(recipe, 'description') and recipe.description:
            ui.label(recipe.description).classes('text-body2 q-mt-xs')

        ui.separator().classes('q-my-sm')

        # Metadata badges
        with ui.row().classes('q-gutter-xs flex-wrap'):
            if hasattr(recipe, 'methodology') and recipe.methodology:
                ui.badge(recipe.methodology, color='primary').props('outline')
            if hasattr(recipe, 'output_type') and recipe.output_type:
                ui.badge(recipe.output_type, color='secondary').props('outline')
            if hasattr(recipe, 'tags') and recipe.tags:
                for tag in recipe.tags[:4]:
                    ui.badge(tag, color='grey-6').props('outline')

        # Steps
        if hasattr(recipe, 'steps') and recipe.steps:
            ui.label(f'{len(recipe.steps)} steps:').classes(
                'text-caption text-grey q-mt-sm'
            )
            with ui.column().classes('q-gutter-none q-ml-sm'):
                for i, step in enumerate(recipe.steps, 1):
                    step_type = getattr(step, 'type', 'unknown')
                    step_id = getattr(step, 'id', f'step-{i}')
                    icon = 'smart_toy' if step_type == 'llm_call' else 'code'
                    with ui.row().classes('items-center q-gutter-xs'):
                        ui.icon(icon, size='xs', color='grey')
                        ui.label(f'{i}. {step_id} ({step_type})').classes(
                            'text-caption'
                        )
