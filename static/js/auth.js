const togglePassword = document.getElementById("togglePassword");

const password = document.getElementById("password");

if(togglePassword){

    togglePassword.addEventListener("click",()=>{

        if(password.type==="password"){

            password.type="text";

            togglePassword.innerHTML='<i class="fa-solid fa-eye-slash"></i>';

        }

        else{

            password.type="password";

            togglePassword.innerHTML='<i class="fa-solid fa-eye"></i>';

        }

    });

}