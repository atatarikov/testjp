'use strict';
window.addEventListener('DOMContentLoaded', function () {
    if (document.location.pathname.indexOf('/Payment') + 1) {
        let form = document.forms[0];
        let contractSelect;
        let counterpartySelect;
        counterpartySelect = form.querySelector('select[name="counterparty"]'),
            counterpartySelect.addEventListener('change', functionChange),
            contractSelect = form.querySelector('select[name="contract"]'),
            contractSelect.addEventListener('change', functionChange);
    }

    function functionChange() {
        document.querySelector('button[name="save"]').click();
    }
})