// Attendance Trend

new Chart(
document.getElementById("attendanceChart"),
{

type:"line",

data:{

labels:["Mon","Tue","Wed","Thu","Fri","Sat"],

datasets:[{

label:"Attendance",

data:[90,92,88,95,94,91],

fill:true,

borderWidth:3,

tension:.4

}]

},

options:{

responsive:true,

plugins:{

legend:{

display:false

}

}

}

});

// Department Distribution

new Chart(
    document.getElementById("departmentChart"),
    {
        type: "doughnut",

        data: {
            labels: semesterLabels,

            datasets: [{
                data: semesterValues
            }]
        },

        options: {
            responsive: true
        }
    }
);
// CGPA Distribution

new Chart(
document.getElementById("cgpaChart"),
{

type:"bar",

data:{

labels:["6","7","8","9","10"],

datasets:[{

label:"Students",

data:[8,20,35,18,5]

}]

}

});

// Top Students

new Chart(
document.getElementById("topStudentsChart"),
{

type:"bar",

data:{

labels:["Rahul","Priya","Aman","Neha","Arjun"],

datasets:[{

label:"CGPA",

data:[9.8,9.7,9.6,9.5,9.4]

}]

},

options:{

indexAxis:"y"

}

});