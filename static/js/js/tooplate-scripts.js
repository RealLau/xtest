const width_threshold = 480;

function drawLineChart(data_projects, data_highest, data_high, data_medium, data_low, data_lowest) {
    let lc = $("#lineChart");
    let lc_parent = $(lc).parent();
    if ($(lc).length) {
        $(lc).remove();
        $(lc_parent).append("<canvas id=\"lineChart\"></canvas>");
        ctxLine = document.getElementById("lineChart").getContext("2d");
        optionsLine = {
            scales: {
                yAxes: [
                    {
                        scaleLabel: {
                            display: true,
                            labelString: "BUG数量"
                        },
                        ticks: {
                            min: 0, // it is for ignoring negative step.
                            beginAtZero: true,
                            callback: function (value, index, values) {
                                if (Math.floor(value) === value) {
                                    return value;
                                }
                            }
                        }
                    }
                ]
            }
        };

        // Set aspect ratio based on window width
        optionsLine.maintainAspectRatio =
            $(window).width() < width_threshold ? false : true;

        configLine = {
            type: "line",
            data: {
                labels: data_projects,
                datasets: [

                    {
                        label: "Highest",
                        data: data_highest,
                        fill: false,
                        borderColor: "rgba(255,99,132,1)",
                        cubicInterpolationMode: "monotone",
                        pointRadius: 0
                    },
                    {
                        label: "High",
                        data: data_high,
                        fill: false,
                        borderColor: "rgba(255,222,132,1)",
                        cubicInterpolationMode: "monotone",
                        pointRadius: 0
                    },
                    {
                        label: "Medium",
                        data: data_medium,
                        fill: false,
                        borderColor: "rgba(153, 102, 255, 1)",
                        cubicInterpolationMode: "monotone",
                        pointRadius: 0
                    },
                    {
                        label: "Low",
                        data: data_low,
                        fill: false,
                        borderColor: "rgb(75, 192, 192)",
                        cubicInterpolationMode: "monotone",
                        pointRadius: 0
                    },
                    {
                        label: "Lowest",
                        data: data_lowest,
                        fill: false,
                        borderColor: "rgb(255, 255, 222)",
                        cubicInterpolationMode: "monotone",
                        pointRadius: 0
                    }

                ]
            },
            options: optionsLine
        };

        lineChart = new Chart(ctxLine, configLine);
    }
}

Colors = {};
Colors.names = {
    aqua: "#00ffff",
    azure: "#f0ffff",
    beige: "#f5f5dc",
    black: "#000000",
    blue: "#0000ff",
    brown: "#a52a2a",
    cyan: "#00ffff",
    darkblue: "#00008b",
    darkcyan: "#008b8b",
    darkgrey: "#a9a9a9",
    darkgreen: "#006400",
    darkkhaki: "#bdb76b",
    darkmagenta: "#8b008b",
    darkolivegreen: "#556b2f",
    darkorange: "#ff8c00",
    darkorchid: "#9932cc",
    darkred: "#8b0000",
    darksalmon: "#e9967a",
    darkviolet: "#9400d3",
    fuchsia: "#ff00ff",
    gold: "#ffd700",
    green: "#008000",
    indigo: "#4b0082",
    khaki: "#f0e68c",
    lightblue: "#add8e6",
    lightcyan: "#e0ffff",
    lightgreen: "#90ee90",
    lightgrey: "#d3d3d3",
    lightpink: "#ffb6c1",
    lightyellow: "#ffffe0",
    lime: "#00ff00",
    magenta: "#ff00ff",
    maroon: "#800000",
    navy: "#000080",
    olive: "#808000",
    orange: "#ffa500",
    pink: "#ffc0cb",
    purple: "#800080",
    violet: "#800080",
    red: "#ff0000",
    silver: "#c0c0c0",
    white: "#ffffff",
    yellow: "#ffff00"
};
Colors.random = function () {
    var result;
    var count = 0;
    for (var prop in this.names)
        if (Math.random() < 1 / ++count)
            result = prop;
    return result;
};

function drawBarChart(modules, modules_data) {
    let bc = $("#barChart");
    let bc_parent = $(bc).parent();
    let bg_colors = [];
    for (let i = 0; i < modules.length; i++) {
        let c = Colors.names[Colors.random()];
        while (true) {
            if (!bg_colors.includes(c)) {
                bg_colors.push(c);
                break;
            } else {
                c = Colors.names[Colors.random()];
            }
        }
    }
    if ($(bc).length) {
        $(bc).remove();
        $(bc_parent).append("<canvas id=\"barChart\"></canvas>");
        ctxBar = document.getElementById("barChart").getContext("2d");

        optionsBar = {
            responsive: true,
            scales: {
                yAxes: [
                    {
                        barPercentage: 0.2,
                        ticks: {
                            min: 0, // it is for ignoring negative step.
                            beginAtZero: true
                        },
                        scaleLabel: {
                            display: true,
                            labelString: "模块"
                        }
                    }
                ],
                xAxes: [
                    {
                        ticks: {
                            beginAtZero: true, min: 0, callback: function (value, index, values) {
                                if (Math.floor(value) === value) {
                                    return value;
                                }
                            }
                        },

                    }
                ]
            }
        };

        optionsBar.maintainAspectRatio =
            $(window).width() < width_threshold ? false : true;

        configBar = {
            type: "horizontalBar",
            data: {
                // labels: ["Red", "Aqua", "Green", "Yellow", "Purple", "Orange", "Blue"],
                labels: modules,
                datasets: [
                    {
                        label: "BUG数量",
                        // data: [33, 40, 28, 49, 58, 38, 44],
                        data: modules_data,
                        backgroundColor: bg_colors,
                        borderWidth: 0
                    }
                ]
            },
            options: optionsBar
        };

        barChart = new Chart(ctxBar, configBar);
    }
}

function drawPieChart(data_level) {
    // 先删除原来的canvas，否则会有缓存，鼠标移动到图上时，会出现上一次的图
    let pc = $("#pieChart");
    if ($(pc).length) {
        $(pc).remove();
        let pcc = $("#pieChartContainer");
        $(pcc).append("<canvas id=\"pieChart\" class=\"chartjs-render-monitor\" width=\"200\" height=\"200\"></canvas>");
        var chartHeight = 300;
        $(pcc).css("height", chartHeight + "px");

        ctxPie = document.getElementById("pieChart").getContext("2d");

        optionsPie = {
            responsive: true,
            maintainAspectRatio: false,
            layout: {
                padding: {
                    left: 10,
                    right: 10,
                    top: 10,
                    bottom: 10
                }
            },
            legend: {
                position: "top"
            }
        };
        configPie = {
            type: "pie",
            data: {
                datasets: [
                    {
                        data: data_level,
                        backgroundColor: ["#F7604D", "#F1A041", "#4ED6B8", "#A8D582", "#00FF00"],
                        label: "Level"
                    }
                ],
                labels: [
                    "Highest",
                    "High",
                    "Medium",
                    "Low",
                    "Lowest"
                ]
            },
            options: optionsPie
        };

        pieChart = new Chart(ctxPie, configPie);
    }
}

function drawExecuteBar(data_executors, data_bug_count, data_process) {

    var ec = $("#Chart-caseExecution");
    var ec_parent = $(ec).parent();
    if ($(ec).length) {
        $(ec).remove();
        $(ec_parent).append("<canvas id=\"Chart-caseExecution\"></canvas>");
        ctxBar = document.getElementById("Chart-caseExecution").getContext("2d");
        bg_colors_bug_count = [];
        bg_colors_process = [];
        for (let i = 0; i < data_executors.length; i++) {
            bg_colors_bug_count.push("#FFFFFF");
            bg_colors_process.push("#EEEE00");
        }
        new Chart(ctxBar, {
            type: 'bar',
            data: {
                labels: data_executors,
                datasets: [{
                    label: 'BUG数量',
                    yAxisID: 'BUG数量',
                    data: data_bug_count,
                    backgroundColor: bg_colors_bug_count,
                }, {
                    label: '当前进度(%)',
                    yAxisID: '当前进度',
                    data: data_process,
                    backgroundColor: bg_colors_process,

                }]
            },
            options: {
                scales: {
                    yAxes: [{
                        id: 'BUG数量',
                        type: 'linear',
                        position: 'left',
                        ticks:{
                            min:0,
                            beginAtZero: true,
                            callback: function (value, index, values) {
                                if (Math.floor(value) === value) {
                                    return value;
                                }
                            }
                        }
                    }, {
                        id: '当前进度',
                        type: 'linear',
                        position: 'right',
                        ticks: {
                            max: 100,
                            min: 0
                        }
                    }]
                }
            }
        });
    }


}

function updateLineChart() {
    if (lineChart) {
        lineChart.options = optionsLine;
        lineChart.update();
    }
}
