(() => {
    const categorySelect = document.getElementById("id_categoria");
    const customType = document.getElementById("custom-type-container");
    const customInput = document.getElementById("id_tipo_personalizado");

    const updateCustomType = () => {
        const showCustomType = categorySelect.value === "otros";
        customType.hidden = !showCustomType;
        customInput.required = showCustomType;
    };

    if (categorySelect) {
        categorySelect.addEventListener("change", updateCustomType);
        updateCustomType();
    }
})();