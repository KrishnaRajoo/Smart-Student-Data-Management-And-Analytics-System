const studentChart = document.getElementById("studentChart");

if(studentChart){

new Chart(studentChart,{

type:"line",

data:{

labels:["Jan","Feb","Mar","Apr","May","Jun"],

datasets:[{

label:"Students",

data:[120,180,250,320,410,500],

borderWidth:3,

fill:false

}]

}

});

}

const departmentChart = document.getElementById("departmentChart");

if(departmentChart){

new Chart(departmentChart,{

type:"doughnut",

data:{

labels:["CSE","AI & DS","ECE","ME"],

datasets:[{

data:[35,25,20,20]

}]

}

});

}