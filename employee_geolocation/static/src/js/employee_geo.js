odoo.define('employee_geolocation.geolocation', function (require) {

    "use strict";

    var core = require('web.core');
    var Model = require('web.Model');
    var Widget = require('web.Widget');
    var WidgetAttendances = require('hr_attendance.my_attendances');

    var QWeb = core.qweb;
    var _t = core._t;

    WidgetAttendances.include({
        init: function (parent, action) {
            this._super.apply(this, arguments);
            this.location = [];
            this.errorCode = null;
        },
        update_attendance: function () {
            console.log('ha entrado aqui');
            var self = this;

            var options = {
                enableHighAccuracy: true,
                timeout: 5000,
                maximumAge: 0
            };

             if (navigator.geolocation) {
                 navigator.geolocation.getCurrentPosition(self._manual_attendance.bind(self), self._getPositionError, options);
             }

//            self._manual_attendance({coords: {latitude: 17.55, longitude: 55.09}});

        },
        _manual_attendance: function (position) {
            var self = this;
            var hr_employee = new Model('hr.employee');

            this.location.push(position.coords.latitude);
            this.location.push(position.coords.longitude);

            var hr_employee = new Model('hr.employee');
            hr_employee.call('attendance_manual',
                [[self.employee.id], 'hr_attendance.hr_attendance_action_my_attendances', false, this.location]
            ).then(function (result) {
                if (result.action) {
                    self.do_action(result.action);
                } else if (result.warning) {
                    self.do_warn(result.warning);
                }
            });
        },
        _getPositionError: function (error) {
            console.warn(`ERROR(${error.code}): ${error.message}`);
        },

    });

});