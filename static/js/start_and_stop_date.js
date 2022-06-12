'use strict';
window.addEventListener('DOMContentLoaded', function() {
let form = document.forms[0];
let dateStart = form.querySelector('input[name="date_start"]');
let dateStop = form.querySelector('input[name="date_stop"]');
let curDate = new Date();
if (dateStart.value==''){
    dateStart.value = curDate.getFullYear() + '-' + (curDate.getMonth()+1) + '-' + curDate.getDate();
}
if (dateStop.value==''){
    dateStop.value = curDate.getFullYear() + '-' + (curDate.getMonth()+2) + '-' + curDate.getDate();
}
})