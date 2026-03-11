function addToCal(value) {
    if (value === '=') {
        document.getElementById('display').value = eval(document.getElementById('display').value);
    } else if (value === 'C') {
        document.getElementById('display').value = "";
    } else {
        document.getElementById('display').value += value;
    }
}
