
// select starting options
let colorStyle = "default"; // "default" or "palette"
let radialColorStart = 200;
let mapScale = 1.3; // initial map scale;
let production = false;


// 🔽 ⛔ DO NOT MODIFY NEXT LINES
let { nodes, edges } = createNodesEdges(outlineText);
[physicsEnabled, positionAcquired, dragNodes] = production ? [false, true, false] : [true, false, true];
const data = { nodes: nodes, edges: edges };
const centralNode = nodes.find(n => n.id === 1);
// 🔼 ⛔ DO NOT MODIFY ABOVE LINES


// NOTE: to get positions execute "network.getPositions();" on the console
positions = {"1":{"x":-142,"y":-20},"2":{"x":-548,"y":-57},"3":{"x":-556,"y":-390},"4":{"x":-562,"y":298},"5":{"x":-940,"y":42},"6":{"x":285,"y":-8},"7":{"x":606,"y":-325},"8":{"x":655,"y":-46},"9":{"x":380,"y":389},"10":{"x":599,"y":231},"11":{"x":2,"y":-404},"12":{"x":411,"y":-536},"13":{"x":-325,"y":-474},"14":{"x":-147,"y":-683},"15":{"x":181,"y":-747},"16":{"x":-95,"y":381},"17":{"x":-93,"y":761},"18":{"x":213,"y":611},"19":{"x":-445,"y":637}}


const options = {
    nodes: {
        shape: 'box',
        // Node shape options:
        // with label inside: ellipse, circle, database, box, text
        // with label outside: image, circularImage, diamond, dot, star, triangle, triangleDown, hexagon, square and icon
        widthConstraint: { maximum: 150 }, // Max width for nodes
        font: {
            size: 18,
            face: 'Georgia',
            multi: 'html',
            color: 'yellow',
            mod: 'bold'
        },
        borderWidth: 2,
        shadow: true
    },
    edges: {
        arrows: 'to', // Arrow direction: to, from, middle or any combination
        width: 2,
        selectionWidth: 4,
        smooth: {type: 'continuous'} // Edge curve style
    },
    physics: {
        enabled: true,
        barnesHut: {
            gravitationalConstant: -5000,
            centralGravity: 0.1,
            springLength: 110,
            springConstant: 0.04,
            damping: 0.15,
            avoidOverlap: 0.05
        },
        stabilization: {
            iterations: 250,
            fit: true
        }
    },
    interaction:{
        dragNodes:dragNodes,
        zoomView: true,
    }
};
centralNode.shape ='ellipse';
centralNode.color = 'hsl(240, 100%, 50%)';
centralNode.font = { color: 'yellow', size: 26 }
