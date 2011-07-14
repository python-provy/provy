var moduleDocTemplate = null;
var roleDocTemplate = null;
var methodDocTemplate = null;
var currentDoc = null
var osLinks = null

$(function() {
    moduleDocTemplate = $('#module-template');
    roleDocTemplate = $('#role-template');
    methodDocTemplate = $('#method-template');
    currentDoc = $('#current-doc');
    osLinks = $('.operating-systems a');
});

google.load('visualization', '1', {packages:['orgchart']});
google.setOnLoadCallback(getData);
function getData() {
    $.ajax({
        url: 'js/docs.json',
        dataType: 'json',
        cache: false,
        success: function(docs) {
            drawChart(docs);
        }
    });
}

function getRows(docs) {
    var rows = [];
    recurseDocs(docs, '', rows);
    return rows;
}

function recurseDocs(rootNode, parentNode, rows) {
    for (key in rootNode) {
        if (key == '__proto__') continue;
        if (key.substr(0,2) == '__') continue;

        if (rootNode[key]['__methods__'] == null) {
            rows.push([{v:rootNode[key]['__name__'], f:key}, parentNode, rootNode[key]['__name__']]);
            recurseDocs(rootNode[key], rootNode[key]['__name__'], rows)
        }
        else {
            rows.push([{v:rootNode[key]['__fullName__'], f:rootNode[key]['__name__']}, parentNode, rootNode[key]['__fullName__']]);
        }
    }
}

function formatHTML(text) {
    var returnText = []
    var lines = text.split('\n');
    for (var i=0; i<lines.length; i++) {
        var line = lines[i];
        if (line.replace(/\s/gi,'') == '') continue;
        returnText.push('<p>' + line + '</p>');
    }
    return returnText.join('\n');
}

function filterDocs(docs, namespace) {
    var result = docs;
    var names = namespace.split('.');
    for (var i=0; i<names.length; i++){
        result = result[names[i]];
    }
    return result;
}

function drawChart(docs) {
    var filterNamespace = function(namespace) {
        currentDoc.fadeOut('fast');

        var data = new google.visualization.DataTable();
        data.addColumn('string', 'Name');
        data.addColumn('string', 'Parent');
        data.addColumn('string', 'ToolTip');

        var filteredDocs = namespace ? filterDocs(docs, namespace) : docs;
        var rows = getRows(filteredDocs)
        data.addRows(rows);
        var chart = new google.visualization.OrgChart(document.getElementById('docs'));

        var selectHandler = function(e) {
            currentDoc.fadeOut('fast', function() {
                var item = chart.getSelection()[0];
                if (!item) {
                    return;
                }

                var selectedValue = null;
                if (item.row != null && item.column != null) {
                    selectedValue = data.getValue(item.row, item.column);
                } else if (item.row != null) {
                    selectedValue = data.getValue(item.row, 2);
                } else if (item.column != null) {
                    selectedValue = data.getValue(0, item.column);
                }

                var parts = selectedValue.split('.');
                var doc = docs;
                for (var i=0; i<parts.length; i++) {
                    doc = doc[parts[i]];
                }

                if (doc['__methods__'] == null) {
                    var template = moduleDocTemplate.clone();
                    template.find('.name').html(doc['__name__']);

                    var docstring = doc['__doc__'] || 'No documentation found for ' + doc['__name__'] + '.';
                    template.find('.docs').html(formatHTML(docstring));
                } else {
                    var template = roleDocTemplate.clone();
                    template.find('.name').html(doc['__name__'] + ' - ' + doc['__module__']);

                    var docstring = doc['__doc__'] || 'No documentation found for ' + doc['__name__'] + '.';
                    template.find('.docs').html(formatHTML(docstring));

                    var methodContainer = template.find('.methods');
                    for (var i=0; i < doc['__methods__'].length; i++) {
                        var method = doc['__methods__'][i];
                        var methodTemplate = methodDocTemplate.clone();

                        methodTemplate.find('.name').html(method['__name__']);
                        var docstring = method['__doc__'] || 'No documentation found for method ' + method['__name__'] + '.';
                        methodTemplate.find('.docs').html(formatHTML(docstring));

                        methodTemplate.removeAttr('id');
                        methodTemplate.show();
                        methodContainer.append(methodTemplate);
                    }
                }

                currentDoc.html('');
                template.removeAttr('id');
                template.show();
                currentDoc.append(template);
                sh_highlightDocument();
                currentDoc.fadeIn('fast');
            });
        };

        google.visualization.events.addListener(chart, 'select', selectHandler);

        chart.draw(data, {allowHtml:true});
    };

    osLinks.click(function(ev) {
        var link = $(this);
        var namespace = link.attr('data-select');
        filterNamespace(namespace);
    });

    filterNamespace('provy.core');
}

