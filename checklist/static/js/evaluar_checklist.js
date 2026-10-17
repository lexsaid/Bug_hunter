(() => {
            
            const evtForm = document.getElementById("evaluation-form");

            evtForm.addEventListener("submit", (event) => {
                if (!window.confirm("¿Estás seguro de que deseas guardar los cambios?")) {
                    event.preventDefault();
                }
            });
            
        })();