function initPortal() {
    const role = window.safeStorage ? window.safeStorage.get("lunawave_user_role") : localStorage.getItem("lunawave_user_role");
    if (role && role !== "client") {
        store.userRole = role;
    } else {
        store.userRole = "portal";
    }
    applyRoleUI();
}
