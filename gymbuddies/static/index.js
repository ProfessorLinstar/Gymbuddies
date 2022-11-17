import "/tui-calendar/dist/tui-calendar.min.css";
import "/tui-time-picker/dist/tui-time-picker.min.css";
import "/tui-date-picker/dist/tui-date-picker.min.css";

// import Calendar from "tui-calendar";
import Calendar from "./app.js"



const Calendar = tui.Calendar;
const userEvents = Calendar.returnUserEvents();


const container = document.getElementById('calendar');
const options = {
    defaultView: 'week',
    timezone: {
        zones: [
            {
                timezoneName: 'Asia/Seoul',
                displayLabel: 'Seoul',
            },
            {
                timezoneName: 'Europe/London',
                displayLabel: 'London',
            },
        ],
    },
    calendars: [
        {
            id: 'cal1',
            name: 'Personal',
            backgroundColor: '#03bd9e',
        },
        {
            id: 'cal2',
            name: 'Work',
            backgroundColor: '#00a9ff',
        },
    ],
};

const calendar = new Calendar(container, options);

calendar.createEvents([
    {
        id: 'event1',
        calendarId: 'cal2',
        title: 'Weekly meeting',
        start: '2022-06-07T09:00:00',
        end: '2022-06-07T10:00:00',
    },
    {
        id: 'event2',
        calendarId: 'cal1',
        title: 'Lunch appointment',
        start: '2022-06-08T12:00:00',
        end: '2022-06-08T13:00:00',
    },
    {
        id: 'event3',
        calendarId: 'cal2',
        title: 'Vacation',
        start: '2022-06-08',
        end: '2022-06-10',
        isAllday: true,
        category: 'allday',
    },
]);

            // calendar.setOptions({
            // useFormPopup: true,
            // useDetailPopup: true,
            // });