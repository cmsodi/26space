// Define options variable
let startDate;
let endDate;
let allOption;
let pdfOption;
let bookOption;
let scholarOption;
let consultOption;
let newsOption;
let agenciesOption;

let ExaOption;
let ExaCompanyOption;
let ExaTweetOption;
let ExaResearchPaperOption;
let ExaBlogPostOption;
let ExaNewsOption;


function createNodesEdges(outlineText) {
    outlineText = outlineText.replaceAll('# ', '').replaceAll('#', '  '); // from '#' notation to '  '  
    let lines = outlineText.trim().split('\n');
    let nodes = [];
    let edges = [];
    let stack = [];
    let id = 1;

    lines.forEach(line => {
        let level = line.search(/\S/);
        let label = line.trim();
        let node = { id: id, label: label.split(";")[0], title: label.split(";")[1] };
        nodes.push(node);

        while (stack.length > 0 && stack[stack.length - 1].level >= level) {
            stack.pop();
        }

        if (stack.length > 0) {
            let edge = { from: stack[stack.length - 1].id, to: id };
            edges.push(edge);
        }

        stack.push({ id: id, level: level });
        id += 1;
    });

    nodes[0].title = nodes[0].label;

    return { nodes, edges };
}


function updateNodePositions(nodes, positions) {
    nodes.forEach(node => {
        if (positions[node.id]) {
            node.x = positions[node.id].x;
            node.y = positions[node.id].y;
        }
    });
}


function paletteNodeColors(nodes) {
    const vividColors = [
        'hsl(240, 100%, 40%)',   // Darker Blue
        'hsl(270, 100%, 40%)',   // Darker Violet
        'hsl(300, 100%, 40%)',   // Darker Magenta
        'hsl(330, 100%, 40%)',   // Darker Rose
        'hsl(0, 100%, 40%)',     // Darker Red
        'hsl(30, 100%, 40%)',    // Darker Orange
        'hsl(180, 100%, 30%)',   // Darker Cyan
        'hsl(210, 100%, 40%)',   // Darker Azure
        'hsl(120, 100%, 30%)',   // Darker Green
        'hsl(150, 100%, 30%)',   // Darker Spring Green
        'hsl(60, 100%, 35%)',    // Darker Yellow

    ];

    nodes.forEach((node, index) => {
        node.color = vividColors[index % vividColors.length];
        node.font = { color: 'white' };
    });
    // const centralNode = nodes.find(n => n.id === rootId); //check n. id
    // centralNode.color = 'hsl(240, 100%, 50%)';
    // centralNode.font = { color: 'yellow', size: 32 }

}

function updateNodeColors(nodes, edges, rootId) {
    // Level 1 nodes
    const level1Nodes = nodes.filter(n => n.id !== 1);
    level1Nodes.forEach((node, i) => {
        let hue = radialColorStart + (i * radialColorStart / level1Nodes.length);
        if (hue > 360) { hue = hue - 360; }
        node.color = `hsl(${hue}, 100%, 40%)`;
    });

    // Level 1 edges
    const level1Edges = edges.filter(e => e.from === 1);
    level1Edges.forEach(edge => {
        edge.color = edge.to.color;
    });

    // Further levels 
    const maxLightness = 71;
    edges.filter(e => e.from !== 1).forEach(edge => {

        // Get parent node color
        const parent = nodes.find(n => n.id === edge.from);
        let [h, s, l] = parent.color.match(/\d+/g).map(Number);

        // Raise lightness by 10% 
        l = Math.min(maxLightness, l + (l * 0.25));

        // Update edge color
        edge.color = `hsl(${h}, ${s}%, ${l}%)`;

        // Update child node color
        const child = nodes.find(n => n.id === edge.to);
        child.color = edge.color;

    });

}


function setDefaultSearchOptions() {
    // Original logic to set default search options
    // Google search box
    let startDateInput = document.getElementById('startDate');
    let endDateInput = document.getElementById('endDate');
    let currentDate = new Date();
    // Set default values
    allOption = true;
    pdfOption = false;
    bookOption = false;
    videoOption = false;
    scholarOption = false;
    consultOption = false;
    newsOption = false;
    agenciesOption = false;

    ExaOption = false;
    ExaCompanyOption = false;
    ExaTweetOption = false;
    ExaResearchPaperOption = false;
    ExaBlogPostOption = false;
    ExaNewsOption = false;

    startDate = new Date();
    startDate.setDate(currentDate.getDate() - 1095);
    endDate = currentDate;
    // 'YYYY-MM-DD' format
    startDateInput.value = startDate.toISOString().substring(0, 10);
    endDateInput.value = endDate.toISOString().substring(0, 10);

    // Event delegation for radio buttons
    document.getElementById('selectoptions').addEventListener('change', (event) => {
        if (event.target.name === 'options') {
            allOption = event.target.id === 'allBtn';
            pdfOption = event.target.id === 'pdfBtn';
            bookOption = event.target.id === 'bookBtn';
            videoOption = event.target.id === 'videoBtn';
            scholarOption = event.target.id === 'scholarBtn';
            consultOption = event.target.id === 'consultBtn';
            newsOption = event.target.id === 'newsBtn';
            agenciesOption = event.target.id === 'agenciesBtn';

            ExaOption = event.target.id === 'ExaBtn';
            ExaCompanyOption = event.target.id === 'ExaCompanyBtn';
            ExaTweetOption = event.target.id === 'ExaTweetBtn';
            ExaResearchPaperOption = event.target.id === 'ExaResearchPaperBtn';
            ExaBlogPostOption = event.target.id === 'ExaBlogPostBtn';
            ExaNewsOption = event.target.id === 'ExaNewsBtn';

        } else if (event.target.id === 'startDate') {
            startDate = new Date(event.target.value);
        } else if (event.target.id === 'endDate') {
            endDate = new Date(event.target.value);
        }
    });
}


function createNetwork(data, options) {
    var container = document.getElementById('mynetwork');
    var network = new vis.Network(container, data, options);
    
    // nodes stay in their new positions once dragged
    network.on("dragEnd", function (params) {
        if (params.nodes.length) {
            network.setOptions({ physics: false });
        }
    });
    
    return network;
}


function handleNetworkInteractions(network, nodes, rootId) {
    // Original logic to handle network interactions
    network.on("doubleClick", function (params) {

        // 'MM-DD-YYYY' format
        let startDateString = startDate.toLocaleDateString('en-US', { month: '2-digit', day: '2-digit', year: 'numeric' });
        let endDateString = endDate.toLocaleDateString('en-US', { month: '2-digit', day: '2-digit', year: 'numeric' });
        // '2023-10-28T11:28:53.260Z' format
        let startPublishedDate = startDate.toISOString();

        // Options search prefixes - use configurable domain for localization
        let searchUrl = '';
        let googleDomain = window.googleSearchDomain || 'com';
        let prefGen = 'https://www.google.' + googleDomain + '/search?&tbs=cdr:1,cd_min:';
        let prefSchol = 'https://scholar.google.com/scholar?&hl=en&as_sdt=0,5&as_ylo=';
        let ExaPrefGen1 = "https://exa.ai/search?q=Here's a comprehensive analysis of "
        let ExaPrefGen2 = " from authoritative sources including government agencies, research institutions, and professional organizations:";

        var nodeId = params.nodes[0];
        var node = nodes.find(n => n.id == nodeId);
        var searchTerm = node.title;

        // Options select
        if (allOption) {
            searchUrl = prefGen + startDateString + ',cd_max:' + endDateString + '&q=' + searchTerm;
        } else if (pdfOption) {
            searchUrl = prefGen + startDateString + ',cd_max:' + endDateString + '&q=' + searchTerm + ' filetype:pdf';
        } else if (newsOption) {
            searchUrl = prefGen + startDateString + ',cd_max:' + endDateString + ',sbd:1&tbm=nws&q=' + searchTerm;
        } else if (bookOption) {
            searchUrl = prefGen + startDateString + ',cd_max:' + endDateString + '&tbm=bks&q=' + searchTerm;
        } else if (videoOption) {
            searchUrl = prefGen + startDateString + ',cd_max:' + endDateString + '&tbm=vid&q=' + searchTerm;
        } else if (scholarOption) {
            searchUrl = prefSchol + startDateString + '&as_yhi=' + endDateString + '&q=' + searchTerm;
        } else if (consultOption) {
            searchUrl = prefGen + startDateString + ',cd_max:' + endDateString + '&q=' + searchTerm + ' site:www.boozallen.com OR site:www.deloitte.com OR site:www.accenture.com OR site:www.pwc.com OR site:www.kpmg.com OR site:www.bain.com OR site:www.mckinsey.com OR site:www.bcg.com OR site:www.atkearney.com OR site:www.rolandberger.com OR site:www.starburst.aero OR site:csps.aerospace.org OR site:space4sight.com OR site:know.space OR site:www.espi.or.at OR site:www.swfound.org OR site:www.sia.org OR site:www.chathamhouse.org OR site:www.iiss.org OR site:www.sipri.org OR site:www.casic.com.cn OR site:eng.cast.cn OR site:www.russianspaceweb.com OR site:spacepolicyonline.com OR site:aerospace.csis.org OR site:www.euroconsult-ec.com';
        } else if (agenciesOption) {
            searchUrl = prefGen + startDateString + ',cd_max:' + endDateString + '&q=' + searchTerm + ' site:www.nasa.gov OR site:en.roscosmos.ru/ OR site:www.esa.int OR site:www.isro.gov.in OR site:global.jaxa.jp OR site:www.cnsa.gov.cn/english OR site:www.asc-csa.gc.ca/eng/ OR site:www.ukspaceagency.gov.uk OR site:www.cnes.fr/en OR site:www.dlr.de/en OR site:www.asi.it/en OR site:www.inta.es/INTA/en OR site:ssa.gov.sa/en';
        } else if (ExaOption) {
            searchUrl = ExaPrefGen1 + searchTerm + ExaPrefGen2 + '&filters={"numResults":30,"domainFilterType":"include","type":"auto","startPublishedDate":"'+ startPublishedDate + '","useAutoprompt":true}&resolvedSearchType=keyword';
        } else if (ExaNewsOption) {
            searchUrl = ExaPrefGen1 + searchTerm + ExaPrefGen2 + '&c=' + 'news' + '&filters={"numResults":30,"domainFilterType":"include","type":"auto","startPublishedDate":"'+ startPublishedDate + '","useAutoprompt":true}&resolvedSearchType=keyword';
        } else if (ExaCompanyOption) {
            searchUrl = ExaPrefGen1 + searchTerm + ExaPrefGen2 + '&c=' + 'company' + '&filters={"numResults":30,"domainFilterType":"include","type":"auto","startPublishedDate":"'+ startPublishedDate + '","useAutoprompt":true}&resolvedSearchType=keyword';
        } else if (ExaResearchPaperOption) {
            searchUrl = ExaPrefGen1 + searchTerm + ExaPrefGen2 + '&c=' + 'research paper' + '&filters={"numResults":30,"domainFilterType":"include","type":"auto","startPublishedDate":"'+ startPublishedDate + '","useAutoprompt":true}&resolvedSearchType=keyword';
        } else if (ExaBlogPostOption) {
            searchUrl = ExaPrefGen1 + searchTerm + ExaPrefGen2 + '&c=' + 'blog post' + '&filters={"numResults":30,"domainFilterType":"include","type":"auto","startPublishedDate":"'+ startDateString + '","useAutoprompt":true}&resolvedSearchType=keyword';
        }

        // display map 
        window.open(searchUrl);

    });
}
