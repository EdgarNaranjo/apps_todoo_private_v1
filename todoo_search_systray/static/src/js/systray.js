odoo.define('search_systray.Search', function(require) {
    "use strict";

    var SystrayMenu = require('web.SystrayMenu');
    var Widget = require('web.Widget');
    var rpc = require('web.rpc');

    var SearchWidget = Widget.extend({
        template: 'SearchWidget',
        sequence: 9999,
        events: {
            'focusin input': '_searchTerm',
            'keyup input': '_searchTerm',
            'click .o_search_results a': '_clearResults',
            'focusout input': '_clearResults',
        },
        _clearResults: function () {
            setTimeout(function (){
                this.$('.o_search_results').html(null);
                this.$('input').val('');
            }, 200);
        },
        _searchTerm: function (ev) {
            var search_term = $(ev.currentTarget).val();
            if (search_term.length < 3) {
                 $('.o_search_results').html(null);
                 return;
            };
            this._rpc({
                 model: 'res.users',
                 method: 'search_terms',
                 args: [search_term],
            }).then(function (res) {
                 var $li_data = [];
                 res.forEach(function (resource) {
                     var modelName = resource.model;
                     var modelNameDisplay = resource.name;
                     var records = resource.records.map(function (rec) {
                         return `<a href="#model=${modelName}&id=${rec[0]}" class="list_link" title="${rec[1]}">${rec[1]}</a>`;
                     }).join('');
                     $li_data.push(`<li class="list-group-item"><p>${modelNameDisplay}:</p><p>${records}</p></li>`);
                 });
                 $('.o_search_results').html($li_data.join(''));
            });
        },
    });

    SystrayMenu.Items.push(SearchWidget);

    return SearchWidget;
});

