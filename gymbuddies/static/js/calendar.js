(function ($) {
  'use strict';

  var DayScheduleSelector = function (el, options) {
    this.$el = $(el);
    this.options = $.extend({}, DayScheduleSelector.DEFAULTS, options);
    this.render();
    this.attachEvents();
    this.$selectingStart = null;
  }


  DayScheduleSelector.DEFAULTS = {
    days        : [0, 1, 2, 3, 4, 5, 6],  // Sun - Sat
    startTime   : '00:00',                // HH:mm format
    endTime     : '24:00',                // HH:mm format
    interval    : 30,                     // minutes
    stringDays  : ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
    template    : '<div class="day-schedule-selector">'         +
                    '<table class="schedule-table">'            +
                      '<thead class="schedule-header"></thead>' +
                      '<tbody class="schedule-rows"></tbody>'   +
                    '</table>'                                  +
                  '<div>',
    interactive : true,
    restricted  : true,
    drag        : false,
  };

  /**
   * Render the calendar UI
   * @public
   */
  DayScheduleSelector.prototype.render = function () {
    this.$el.html(this.options.template);
    this.renderHeader();
    this.renderRows();
  };

  /**
   * Render the calendar header
   * @public
   */
  DayScheduleSelector.prototype.renderHeader = function () {
    var stringDays = this.options.stringDays
      , days = this.options.days
      , html = '';

    $.each(days, function (i, _) { html += '<th>' + (stringDays[i] || '') + '</th>'; });
    this.$el.find('.schedule-header').html('<tr><th></th>' + html + '</tr>');
  };

  /**
   * Render the calendar rows, including the time slots and labels
   * @public
   */
  DayScheduleSelector.prototype.renderRows = function () {
    var start = this.options.startTime
      , end = this.options.endTime
      , interval = this.options.interval
      , days = this.options.days
      , $el = this.$el.find('.schedule-rows');

    $.each(generateDates(start, end, interval), function (i, d) {
      var daysInARow = $.map(new Array(days.length), function (_, i) {
        return '<td class="time-slot" data-time="' + hhmm(d) + '" data-day="' + days[i] + '"></td>'
      }).join();

      $el.append('<tr><td class="time-label">' + hAmPm(d) + '</td>' + daysInARow + '</tr>');
    });
  };

  /**
   * Is the day schedule selector in selecting mode?
   * @public
   */
  DayScheduleSelector.prototype.isSelecting = function () {
    return !!this.$selectingStart;
  }

  DayScheduleSelector.prototype.initialize = function ($slot) { $slot.attr('data-initial', 'selected'); }
  DayScheduleSelector.prototype.select = function ($slot) { $slot.attr('data-selected', 'selected'); }
  DayScheduleSelector.prototype.deselect = function ($slot) { $slot.removeAttr('data-selected'); }

  function isSlotSelected($slot) { return $slot.is('[data-selected]'); }
  function isSlotSelecting($slot) { return $slot.is('[data-selecting]'); }

  /**
   * Get the selected time slots given a starting and a ending slot
   * @private
   * @returns {Array} An array of selected time slots
   */
  function getSelection(plugin, $a, $b) {
    var $slots, small, large, temp;
    if (!$a.hasClass('time-slot') || !$b.hasClass('time-slot')) { return []; }
    $slots = plugin.$el.find('.time-slot[data-day="' + $b.data('day') + '"]');
    large = $slots.index($b);

    $slots = plugin.$el.find('.time-slot[data-day="' + $a.data('day') + '"]');
    small = $slots.index($a);
    if (small > large) { temp = small; small = large; large = temp; }
    console.log("in getSelection: ", small, large);
    return $slots.slice(small, large + 1);
  }

  function getBounds (plugin, $center) {
    var $slots, index, start, end;
    $slots = plugin.$el.find('.time-slot[data-day="' + $center.data('day') + '"]');
    index = $slots.index($center);
    $center.html("")
    for (end = index+1; end < $slots.length && $slots.eq(end).is('[data-selected]'); end++) {
      $slots.eq(end).html("")
    }
    for (start = index-1; start >= 0 && $slots.eq(start).is('[data-selected]'); start--) {
      $slots.eq(start).html("")
    }
    return [
      start == index-1 ? null : [$slots.eq(start+1), $slots.eq(index-1)], 
      end == index+1 ? null : [$slots.eq(index+1), $slots.eq(end-1)]
    ];
  }

  function finalizeSelection(plugin, $target) {
    var $start, $end;
    plugin.$el.find('.time-slot[data-day="' + plugin.$selectingStart.data('day') + '"]').filter('[data-selecting]')
      .attr('data-selected', 'selected').removeAttr('data-selecting');
    plugin.$el.find('.time-slot').removeAttr('data-disabled');
    plugin.$el.trigger('selected.artsy.dayScheduleSelector', [getSelection(plugin, plugin.$selectingStart, $target)]);
    console.log("getBounds:", getBounds(plugin, plugin.$selectingStart));

    [$start, $end] = getBounds(plugin, plugin.$selectingStart);
    $start = $start !== null ? $start[0] : plugin.$selectingStart;
    $end = $end !== null ? $end[1] : plugin.$selectingStart;
    $start.html(formatSlotTime($start, $end));

    plugin.$selectingStart = null;
  }



  DayScheduleSelector.prototype.attachEvents = function () {
    var plugin = this
      , options = this.options;

    if (!options.interactive) {
      this.$el.find(".schedule-rows").find("td").css("cursor", "auto");
      return;
    }

    this.$el.on('click', '.time-slot', function () {
      if (!plugin.isSelecting()) {  // if we are not in selecting mode
        if (options.restricted && !$(this).is("[data-initial]")) return;

        if (isSlotSelected($(this))) {
          plugin.deselect($(this));
          for (const bounds of getBounds(plugin, $(this))) {
            if (bounds !== null) bounds[0].html(formatSlotTime(...bounds))
          }
        } else {  // then start selecting
          plugin.$selectingStart = $(this);
          $(this).attr('data-selecting', 'selecting');
          plugin.$el.find('.time-slot').attr('data-disabled', 'disabled');
          plugin.$el.find('.time-slot[data-day="' + $(this).data('day') + '"]').removeAttr('data-disabled');

          if (!options.drag) finalizeSelection(plugin, $(this));
          else $(this).html(formatSlotTime($(this), $(this)));
        }

      } else {  // if we are in selecting mode
        finalizeSelection(plugin, $(this));
      }
    });

    this.$el.on('mouseover', '.time-slot', function () {
      var $slots, day, start, end, temp;
      if (plugin.isSelecting()) {  // if we are in selecting mode
        day = $(this).data('day');
        $slots = plugin.$el.find('.time-slot[data-day="' + day + '"]');
        end = $slots.index(this);

        day = plugin.$selectingStart.data('day');
        $slots = plugin.$el.find('.time-slot[data-day="' + day + '"]');
        $slots.filter('[data-selecting]').removeAttr('data-selecting');
        start = $slots.index(plugin.$selectingStart);


        if (start > end) { temp = start; start = end; end = temp; }
        $slots.slice(start, end + 1).attr('data-selecting', 'selecting');

        plugin.$selectingStart.html(formatSlotTime($slots.eq(start), $slots.eq(end)));
      }
    });
  };

  /**
   * Serialize the selections
   * @public
   * @returns {Object} An object containing the selections of each day, e.g.
   *    {
   *      0: [],
   *      1: [["15:00", "16:30"]],
   *      2: [],
   *      3: [],
   *      5: [["09:00", "12:30"], ["15:00", "16:30"]],
   *      6: []
   *    }
   */
  DayScheduleSelector.prototype.serialize = function () {
    var plugin = this
      , selections = {};

    $.each(this.options.days, function (_, v) {
      var start, end;
      start = end = false; selections[v] = [];
      plugin.$el.find(".time-slot[data-day='" + v + "']").each(function () {
        // Start of selection
        if (isSlotSelected($(this)) && !start) {
          start = $(this).data('time');
        }

        // End of selection (I am not selected, so select until my previous one.)
        if (!isSlotSelected($(this)) && !!start) {
          end = $(this).data('time');
        }

        // End of selection (I am the last one :) .)
        if (isSlotSelected($(this)) && !!start && $(this).is(".time-slot[data-day='" + v + "']:last")) {
          end = secondsSinceMidnightToHhmm(
            hhmmToSecondsSinceMidnight($(this).data('time')) + plugin.options.interval * 60);
        }

        if (!!end) { selections[v].push([start, end]); start = end = false; }
      });
    })
    return selections;
  };

  function getSlotHours($slot) {
    let time = $slot.data('time').replace(/:00/g, "");
    if (time[0] == "0") {
      time = time.slice(1);
    }
    return time - 0;
  }

  function hoursToAmPm(hours) {
    let ampm = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12;
    return [(hours != 0 ? hours : 12), ampm];
  }

  function formatSlotTime($a, $b) {
    const start = hoursToAmPm(getSlotHours($a));
    const end = hoursToAmPm((getSlotHours($b) + 1) % 24);
    return start[0] + '-' + end.join(' ');
  }

  /**
   * Deserialize the schedule and render on the UI
   * @public
   * @param {Object} schedule An object containing the schedule of each day, e.g.
   *    {
   *      0: [],
   *      1: [["15:00", "16:30"]],
   *      2: [],
   *      3: [],
   *      5: [["09:00", "12:30"], ["15:00", "16:30"]],
   *      6: []
   *    }
   */

  DayScheduleSelector.prototype.deserializeDashboard = function (schedule) {
    var plugin = this, i;
    $.each(schedule, function(d, ds) {
      var $slots = plugin.$el.find('.time-slot[data-day="' + d + '"]');
      $.each(ds, function(_, s) {
        for (i = 0; i < $slots.length; i++) {
          console.log("info", $slots.eq(i).data('time'), s)
          if ($slots.eq(i).data('time') >= s[1]) { break; }
          if ($slots.eq(i).data('time') >= s[0]) { 
            let start = s[0]
            start = start.replace(/:00/g, "")
            if (start[0] == "0") {
              start = start.slice(1)
            }
            let end = s[1]
            end = end.replace(/:00/g, "")
            if (end[0] == "0") {
              end = end.slice(1)
            }
            plugin.select($slots.eq(i)); 
            let matchName = s[2]
            if ($slots.eq(i).data('time') == s[0]) { 
              if (s[2].length > 8) {
                matchName = s[2].slice(0, 5) + "..."
              }
              $slots.eq(i).append(matchName + " " +  hoursToAmPm(start)[0] + "-" + hoursToAmPm(end).join(' '));
            }
          }
        }
      })
    });
  };

  DayScheduleSelector.prototype.deserializeModify = function (schedule) {
    var plugin = this, i;
    $.each(schedule, function(d, ds) {
      var $slots = plugin.$el.find('.time-slot[data-day="' + d + '"]');
      $.each(ds, function(_, s) {
        let start, end;
        for (i = 0; i < $slots.length; i++) {
          if ($slots.eq(i).data('time') >= s[1]) { break; }
          if ($slots.eq(i).data('time') >= s[0]) { 
            end = $slots.eq(i);
            if (!start) start = end;
            plugin.initialize(end);
            if (s[2] == 1) plugin.select(end); 
          } // set events to initialize
        }
        if (start && s[2] == 1) start.html(formatSlotTime(start, end));
      })
    });
  };

  DayScheduleSelector.prototype.deserializeProfile = function (schedule) {
    var plugin = this, i;
    $.each(schedule, function(d, ds) {
      var $slots = plugin.$el.find('.time-slot[data-day="' + d + '"]');
      $.each(ds, function(_, s) {
        let start, end;
        for (i = 0; i < $slots.length; i++) {
          if ($slots.eq(i).data('time') >= s[1]) { break; }
          if ($slots.eq(i).data('time') >= s[0]) {
            end = $slots.eq(i);
            if (!start) start = end;
            plugin.select(end);
          }
        }
        if (start) start.html(formatSlotTime(start, end));
      })
    });
  };

  DayScheduleSelector.prototype.deserializeBuddies = function (schedule) {
    var plugin = this, i;
    $.each(schedule, function(d, ds) {
      var $slots = plugin.$el.find('.time-slot[data-day="' + d + '"]');
      $.each(ds, function(_, s) {
        for (i = 0; i < $slots.length; i++) {
          if ($slots.eq(i).data('time') >= s[1]) { break; }
          if ($slots.eq(i).data('time') >= s[0]) { plugin.initialize($slots.eq(i)); }
        }
      })
    });
  };





  // DayScheduleSelector Plugin Definition
  // =====================================

  function Plugin(option) {
    return this.each(function (){
      var $this   = $(this)
        , data    = $this.data('artsy.dayScheduleSelector')
        , options = typeof option == 'object' && option;

      if (!data) {
        $this.data('artsy.dayScheduleSelector', (data = new DayScheduleSelector(this, options)));
      }
    })
  }

  $.fn.dayScheduleSelector = Plugin;

  /**
   * Generate Date objects for each time slot in a day
   * @private
   * @param {String} start Start time in HH:mm format, e.g. "08:00"
   * @param {String} end End time in HH:mm format, e.g. "21:00"
   * @param {Number} interval Interval of each time slot in minutes, e.g. 30 (minutes)
   * @returns {Array} An array of Date objects representing the start time of the time slots
   */
  function generateDates(start, end, interval) {
    var numOfRows = Math.ceil(timeDiff(start, end) / interval);
    return $.map(new Array(numOfRows), function (_, i) {
      // need a dummy date to utilize the Date object
      return new Date(new Date(2000, 0, 1, start.split(':')[0], start.split(':')[1]).getTime() + i * interval * 60000);
    });
  }

  /**
   * Return time difference in minutes
   * @private
   */
  function timeDiff(start, end) {   // time in HH:mm format
    // need a dummy date to utilize the Date object
    return (new Date(2000, 0, 1, end.split(':')[0], end.split(':')[1]).getTime() -
            new Date(2000, 0, 1, start.split(':')[0], start.split(':')[1]).getTime()) / 60000;
  }

  /**
   * Convert a Date object to time in H format with am/pm
   * @private
   * @returns {String} Time in H:mm format with am/pm, e.g. '9:30am'
   */
  function hAmPm(date) {
    var hours = date.getHours()
      , ampm = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12;
    return (hours != 0 ? hours : 12) + ' ' + ampm;
  }


  /**
   * Convert a Date object to time in HH:mm format
   * @private
   * @returns {String} Time in HH:mm format, e.g. '09:30'
   */
  function hhmm(date) {
    var hours = date.getHours()
      , minutes = date.getMinutes();
    return ('0' + hours).slice(-2) + ':' + ('0' + minutes).slice(-2);
  }

  function hhmmToSecondsSinceMidnight(hhmm) {
    var h = hhmm.split(':')[0]
      , m = hhmm.split(':')[1];
    return parseInt(h, 10) * 60 * 60 + parseInt(m, 10) * 60;
  }

  /**
   * Convert seconds since midnight to HH:mm string, and simply
   * ignore the seconds.
   */
  function secondsSinceMidnightToHhmm(seconds) {
    var minutes = Math.floor(seconds / 60);
    return ('0' + Math.floor(minutes / 60)).slice(-2) + ':' +
           ('0' + (minutes % 60)).slice(-2);
  }

  // Expose some utility functions
  window.DayScheduleSelector = {
    ssmToHhmm: secondsSinceMidnightToHhmm,
    hhmmToSsm: hhmmToSecondsSinceMidnight
  };

})(jQuery);
