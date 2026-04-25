// ===============================
// ANALYTICS ANIMATION FUNCTIONS
// ===============================

export function animateNumber(id,value){

const el = document.getElementById(id)

let start = 0

const step = Math.ceil(value/20)

const interval = setInterval(()=>{

start += step

if(start >= value){

start = value
clearInterval(interval)

}

el.innerText = start

},30)

}