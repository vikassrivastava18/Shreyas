<template>
    <nav class="p-2 navbar">
        <div class="d-flex justify-content-end">
            <router-link to="/ask" class="nav-link text_white px-4 py-1 me-2">
              Ask
            </router-link>

            <router-link to="/dialogue" class="nav-link text_white px-4 py-1 me-2">
                Dialogue
            </router-link>

            <router-link to="/answer" class="nav-link text_white px-4 py-1">
                Answer
            </router-link>
        </div>
    </nav>
</template>

<style>
nav {
    text-align: left;
    border-radius: 5px;
    background: linear-gradient(90deg, #fff 0%, #d3e2ef 50%, #fff 100%);}

.nav-link {
    margin-right: 10px;
    font-size: large;
    color: #000;
}

.router-link-exact-active, .router-link-active {
    background-color: #7ef473;
    border: none;
    color: #000;
}

.text_white {
    color: #000;
}

.navbar {
    color: #000;
}
</style>