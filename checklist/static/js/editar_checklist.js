(() => {
            const addButton = document.getElementById("edit-add-row");
            const rows = document.getElementById("edit-criteria-rows");
            const template = document.getElementById("edit-empty-row-template");
            const totalForms = document.getElementById("id_form-TOTAL_FORMS");
            const editForm = document.getElementById("edit-checklist-form");

            addButton.addEventListener("click", () => {
                const index = Number(totalForms.value);
                const row = template.content.cloneNode(true);
                row.querySelectorAll("[name], [id], label[for]").forEach((element) => {
                    for (const attribute of ["name", "id", "for"]) {
                        if (element.hasAttribute(attribute)) {
                            element.setAttribute(
                                attribute,
                                element.getAttribute(attribute).replace(/__prefix__/g, index)
                            );
                        }
                    }
                });
                row.querySelector(".row-number").textContent = index + 1;
                rows.appendChild(row);
                totalForms.value = index + 1;
            });

            editForm.addEventListener("submit", (event) => {
                if (!window.confirm("¿Estás seguro de que deseas guardar los cambios?")) {
                    event.preventDefault();
                }
            });
            
        })();