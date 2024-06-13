/** @odoo-module **/


import publicWidget from "@web/legacy/js/public/public_widget";
import Dialog from '@web/legacy/js/core/dialog';
import { _t } from "@web/core/l10n/translation";
var token = null;


publicWidget.registry.FavoriteItem = publicWidget.Widget.extend({
    selector: '.new_timesheet',
    events: {
        'change select[name="project"]': '_onChangeProject',
        'change select[name="tasks"]': '_onChangeTask',

    },

    _onChangeProject: function(ev) {
        var project = $(ev.currentTarget).val();

        $.ajax({
            type: "POST",
            dataType: 'json',
            url: '/timesheet/form/project',
            contentType: "application/json; charset=utf-8",
            data: JSON.stringify({
                'jsonrpc': "2.0",
                'method': "call",
                "params": { project_id: project }
            }),
            success: function(data) {
                if (data.result) {
                    $('#task_div').replaceWith(data.result.datas);
                }
            },
        });
    },
    _onChangeTask: function(ev) {
        var task = $(ev.currentTarget).val();
        $('input[name="task_id"]').val(task);

    },
});

$('.sheet_select').on('click', '#date_id', function(event) {
    $('#contact').click();
});

$('.tmk_timesheet_table').on("click", "#delete_timesheet", function(event) {
    var timesheet_id = $(this).parents("tr").find('input[name="timesheet_id"]').val()
    $('#timesheet_delete').val(timesheet_id);
    $('#ModalDeleteTimesheet').modal('show');
});


$('.tmk_timesheet_table').on("click", "#edit_timesheet", function(event) {
    $('#timesheet_edit').val($(this).parents("tr").find('input[name="timesheet_id"]').val());
    $('#project_input').val($(this).parents("tr").find('input[name="timesheet_project_id"]').val());
    $('#task_input').val($(this).parents("tr").find('input[name="timesheet_task_id"]').val());
    var timesheet_date_element =$(this).parents("tr").find('input[name="timesheet_date"]');
    var lang = $(this).parents("tr").find('input[name="timesheet_format"]').val();
    if(timesheet_date_element){
        var dateString = timesheet_date_element.val();
        var dateParts = dateString.split('-');
        if (lang == 'es') {
            var formattedDateString = `${dateParts[2]}/${dateParts[1]}/${dateParts[0]}`;
        }
        else {
            var formattedDateString = `${dateParts[1]}/${dateParts[2]}/${dateParts[0]}`;
        }
        $('#timesheet_date_elem').val(formattedDateString);
    }
    var timesheet_hexa = $(this).parents("tr").find('input[name="timesheet_unit_amount"]');
    if(timesheet_hexa){
        var value_hexa = timesheet_hexa.val();
        // Obtain the integer part of hours
        var hours = Math.floor(value_hexa);
        // Obtain the integer part of hours and convert to minutes
        var minutes = Math.round((value_hexa - hours) * 60);
        // Make sure the hours and minutes are in two-digit format
        var formattedHours = hours.toString().padStart(2, '0');
        var formattedMinutes = minutes.toString().padStart(2, '0');
        // Combine hours and minutes in HH:MM format
        var timesheet_unit_amount = `${formattedHours}:${formattedMinutes}`;
    }
    $('#time').val(timesheet_unit_amount);
    $('#note').val($(this).parents("tr").find('input[name="timesheet_name"]').val());
    $('#ModalEditTimesheet').modal('show');
});
