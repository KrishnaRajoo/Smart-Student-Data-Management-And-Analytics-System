// =============================
// Animated Counter
// =============================

const counters = document.querySelectorAll(".counter");

counters.forEach(counter => {

    const target = Number(counter.getAttribute("data-target"));

    let current = 0;

    const speed = target / 120;

    const updateCounter = () => {

        if(current < target){

            current += speed;

            counter.innerText = Math.ceil(current);

            requestAnimationFrame(updateCounter);

        }

        else{

            counter.innerText = target;

        }

    };

    updateCounter();

});