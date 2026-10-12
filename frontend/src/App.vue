<template>
    <main>
        <div class="container my-2" id="mainContent">
            <div class="innerContainer p-2">
                <header>
                    <HeaderComponent />                    
                </header>

                <NavComponent />

                <div class="tab-content mt-2" id="routeContent">
                    <RouterView />                  
                </div>
            </div>
        </div>
    </main>
  
</template>

<script setup>
import HeaderComponent from './components/HeaderComponent.vue';
import NavComponent from './components/NavComponent.vue';

</script>

<style scoped>
    #mainContent {
        background: white;
        border: 1px dotted #dfdfdf;
        border-radius: 10px;
        box-shadow: 0 5px 40px rgb(0, 0, 0, 4%);
        height: 100%; 
        
    }

    #mainContent {
        min-height: 100vh;
    }

    h2, h3, h4 {
        font-weight: 400;
    }

    #routeContent {
        border: 1px dotted;
        border-radius: 10px;
        min-height: 80vh;
        background-color: #f9fbf8;       
    }

</style>
