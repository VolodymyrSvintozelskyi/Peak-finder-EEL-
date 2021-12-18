var file_content = undefined;

// ["canvas_pl", "canvas_ma", "canvas_fit"];
var num_of_tabs = 5;
var tab_active = new Array(num_of_tabs).fill(false);
var tab_plots = new Array(num_of_tabs).fill(undefined);
var tab_layouts = new Array(num_of_tabs).fill(undefined);
var tab_current = 0;
var tab_prev_current = 0;
var selected_range = false;

function updateGui(evt=undefined){
    console.log(selected_range)
    ma_apply = document.getElementById("ma-apply").checked;
    second_der_apply = document.getElementById("second-deriv-apply").checked;
    smoothing_apply = document.getElementById("smoothing-apply").checked;
    autofit_apply = document.getElementById("auto-finder-apply").checked;
    manfit_apply = document.getElementById("man-finder-apply").checked;
    let file_column = document.getElementById("file-column").value;
    let ma_width = document.getElementById("ma-width").value;
    let ma_iter = document.getElementById("ma-iter").value;
    let second_p = document.getElementById("second_p").value;
    let second_a1 = document.getElementById("second_a1").value;
    let second_a2 = document.getElementById("second_a2").value;
    let second_a3 = document.getElementById("second_a3").value;
    let smooth_width = document.getElementById("smooth_width").value;
    let smooth_iter = document.getElementById("smooth_iter").value;
    let autofit_sep = document.getElementById("autofit_sep").value;
    let autofit_active = document.getElementById("autofit_active").value;
    let autofit_max_peaks = document.getElementById("autofit_max_peaks").value;
    let autofit_ampl_thr = document.getElementById("autofit_ampl_thr").value;
    let manfit_ampl_thr = document.getElementById("manfit_ampl_thr").value;
    let manfit_num_peaks = document.getElementById("manfit_num_peaks").value;

    if (!isInteger(ma_width)) document.getElementById("ma-width").reportValidity("Incorrect value");
    if (!isInteger(ma_iter)) document.getElementById("ma-iter").reportValidity("Incorrect value");
    if (!isInteger(second_p)) document.getElementById("second_p").reportValidity("Incorrect value");
    if (!isInteger(smooth_width)) document.getElementById("smooth_width").reportValidity("Incorrect value");
    if (!isInteger(smooth_iter)) document.getElementById("smooth_iter").reportValidity("Incorrect value");
    if (!isInteger(autofit_sep)) document.getElementById("autofit_sep").reportValidity("Incorrect value");
    if (!isInteger(autofit_active)) document.getElementById("autofit_active").reportValidity("Incorrect value");
    if (!isInteger(autofit_max_peaks)) document.getElementById("autofit_max_peaks").reportValidity("Incorrect value");
    if (!isInteger(manfit_num_peaks)) document.getElementById("manfit_num_peaks").reportValidity("Incorrect value");

    if (0 > ma_width){ document.getElementById("ma-width").reportValidity("Incorrect value");}
    if (0 > ma_iter){ document.getElementById("ma-ma_iter").reportValidity("Incorrect value");}
    if (0 > second_p) document.getElementById("second_p").reportValidity("Incorrect value");
    if (0 > smooth_width) document.getElementById("smooth_width").reportValidity("Incorrect value");
    if (0 > smooth_iter) document.getElementById("smooth_iter").reportValidity("Incorrect value");
    if (0 > autofit_sep) document.getElementById("autofit_sep").reportValidity("Incorrect value");
    if (0 > autofit_max_peaks) document.getElementById("autofit_max_peaks").reportValidity("Incorrect value");
    if (0 > manfit_num_peaks) document.getElementById("manfit_num_peaks").reportValidity("Incorrect value");
    if (0 > second_a1) document.getElementById("second_a1").reportValidity("Incorrect value");
    if (0 > second_a2) document.getElementById("second_a2").reportValidity("Incorrect value");
    if (0 > second_a3) document.getElementById("second_a3").reportValidity("Incorrect value");
    if (0 > autofit_ampl_thr) document.getElementById("autofit_ampl_thr").reportValidity("Incorrect value");
    if (0 > manfit_ampl_thr) document.getElementById("manfit_ampl_thr").reportValidity("Incorrect value");
    
    if (! file_content) return;
    request = {
        "ma_apply": ma_apply,
        "second_der_apply": second_der_apply,
        "smoothing_apply": smoothing_apply,
        "autofit_apply": autofit_apply,
        "manfit_apply": manfit_apply,
        "file_column": parseInt(file_column),
        "ma_width": parseInt(ma_width),
        "ma_iter": parseInt(ma_iter),
        "second_p": parseInt(second_p),
        "second_a1": parseFloat(second_a1),
        "second_a2": parseFloat(second_a2),
        "second_a3": parseFloat(second_a3),
        "smooth_width": parseInt(smooth_width),
        "smooth_iter": parseInt(smooth_iter),
        "autofit_sep": parseInt(autofit_sep),
        "autofit_active": parseInt(autofit_active),
        "autofit_max_peaks": parseInt(autofit_max_peaks),
        "autofit_ampl_thr": parseFloat(autofit_ampl_thr),
        "manfit_num_peaks": parseInt(manfit_num_peaks),
        "manfit_ampl_thr": parseInt(manfit_ampl_thr),
        "manfit_selected_range": selected_range,
    }
    eel.update(request, file_content)
}

function loadfile(evt){
    var file = evt.target.files[0];
    document.getElementById("file-name").innerHTML = file.name;
    if (file) {
        var reader = new FileReader();
        reader.readAsText(file, "UTF-8");
        reader.onload = function (evt) {
            file_content = evt.target.result;
            updateGui()
        }
        reader.onerror = function (evt) {
            alert("File reading error");
        }
    }else{
        alert("File reading error");
    }
}

function updateTabs(){
    tablinks = document.getElementsByClassName("tablinks");
    for (i = 0; i < tablinks.length; i++) {
        if (tab_active[i] && file_content) {
            tablinks[i].style.display = "block";
        }else{
            tablinks[i].style.display = "none";
        }
    }
    if (tab_active[tab_current]){
        if (document.getElementById("canvas").className == "js-plotly-plot" && tab_prev_current == tab_current){
            tab_layouts[tab_current]["uirevision"] = "Hello"
            Plotly.react("canvas", tab_plots[tab_current], tab_layouts[tab_current]);
        }else{
            tab_layouts[tab_current]["uirevision"] = "Hello"
            Plotly.newPlot("canvas", tab_plots[tab_current], tab_layouts[tab_current]);
        }
        tab_prev_current = tab_current
    }
    if (tab_active[0]){
        document.getElementById("canvas").on('plotly_selected', function(eventData) {
            selected_range = eventData.range;  
            updateGui()  
        }
        );
    }
    
}

function openTab(evt, tabName) {
    let i, tablinks;
    tablinks = document.getElementsByClassName("tablinks");
    for (i = 0; i < tablinks.length; i++) {
      tablinks[i].className = tablinks[i].className.replace(" active", "");
    }
    tab_current = tabName;
    updateTabs();
    evt.currentTarget.className += " active";
}

function isInteger(n){
    return Number(n) === n && n % 1 === 0;
}

updateTabs();
document.getElementById("spectra").addEventListener('change', loadfile, false);
menu_inputs = document.getElementsByClassName("menu-input");
for (i=0;i<menu_inputs.length;i++)
    menu_inputs[i].addEventListener('change', updateGui, false);
menu_checks = document.getElementsByClassName("menu-check");
for (i=0;i<menu_checks.length;i++)
    menu_checks[i].addEventListener('change', updateGui, false);

function autofitenablelistener(){
    if (document.getElementById("second-deriv-apply").checked || document.getElementById("smoothing-apply").checked){
        document.getElementById("auto-finder-apply").disabled = false;
    }else{
        document.getElementById("auto-finder-apply").disabled = true;
    }
}
autofitenablelistener()
document.getElementById("second-deriv-apply").addEventListener("change",autofitenablelistener, false)
document.getElementById("smoothing-apply").addEventListener("change",autofitenablelistener, false)

eel.expose(update_data);
function update_data(datasets, maxcols, error_msg) {
    console.log("Error msg " + error_msg)
    tab_active = new Array(num_of_tabs).fill(false);
    for (i = 0; i<datasets.length; i++){
        tab_plots[datasets[i]["key"]] = datasets[i]["data"];
        tab_layouts[datasets[i]["key"]] = datasets[i]["layout"];
        tab_active[datasets[i]["key"]] = true;
    }
    if (!tab_active[tab_current])
        tab_current = 0;
    updateTabs();
    document.getElementById("file-column").max = maxcols;
    document.getElementById("statusbar").innerHTML = error_msg;
    if (error_msg)
        document.getElementById("statusbar").style.display = "inline-block";
    else    
        document.getElementById("statusbar").style.display = "none";
}

// eel.expose(update_selected_fit);
// function update_selected_fit(data) {
//     if (! tab_active[0]) return;

// }

