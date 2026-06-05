console.log("ERP Dashboard Loaded");


/* =========================
   LOADING OVERLAY
========================= */

function showLoading() {

    const loader = document.getElementById(
        'loadingOverlay'
    );

    if(loader){

        loader.style.display = 'flex';

    }
}


/* =========================
   FILTER FORM
========================= */

const filterForm = document.getElementById(
    'filterForm'
);

if(filterForm){

    filterForm.addEventListener(

        'submit',

        function(){

            showLoading();

        }

    );

}


/* =========================
   SIDEBAR ACTIVE STATE
========================= */

const currentPage = window.location.pathname;

const navLinks = document.querySelectorAll(
    '.sidebar a'
);

navLinks.forEach(link => {

    if(link.getAttribute('href') === currentPage){

        link.classList.add('active-link');

    }

});


/* =========================
   MONTH NAVIGATION
========================= */

const months = [

    'Jan','Feb','Mar','Apr',
    'May','Jun','Jul','Aug',
    'Sep','Oct','Nov','Dec'

];

function nextMonth(){

    const monthSelect = document.getElementById(
        'monthSelect'
    );

    let current = monthSelect.value;

    let index = months.indexOf(current);

    if(index < 11){

        monthSelect.value = months[index + 1];

    }

}

function previousMonth(){

    const monthSelect = document.getElementById(
        'monthSelect'
    );

    let current = monthSelect.value;

    let index = months.indexOf(current);

    if(index > 0){

        monthSelect.value = months[index - 1];

    }

}