"use strict"

let setting;
 fetch('./setting.json')
.then(response => response.json())
.then(data => getSetting(data))
.catch(error => console.log(error))

function getSetting (data) {
    setting = data
    console.log(setting)
let python_path = setting.python_path
let alas_target = setting.alas_target

$("div#starter").append(`<form>
<label for="fname">Python Path:</label>
<input type="text" id="pythonPath" value=${python_path}><br>
<label for="lname">Alas address(IP:PORT):</label>
<input type="text" id="alasAddress" value=${alas_target}><br><br>
</form> `);
}

