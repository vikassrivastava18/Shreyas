<template>
    <div>
        <div class="container px-4">
            <i class="py-4">
            <label for="askLabel" class="control-label p-2 py-4"
            id="askLabel">
                <b>Answer subjective questions on a topic!</b>
            </label>
        </i>
            <SelectComponent @startDialogue="fetchDialogue" class="px-2" />
        </div>

        <div class="container">
            <div v-html="renderMarkdownToHtml" class="p-4 mb-5"></div>
            <div v-if="aiLoading" class="d-flex justify-content-center mt-4">
                <div class="spinner-grow text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            </div>
            <input class="form-control py-2 my-2" id="askInput" 
                v-model="userInput" placeholder="Enter your answer here..."
                @keyup.enter="reviewAnswer" :hidden="inputDisabled">            
        </div>
    </div>
</template>

<script setup>
import { ref, getCurrentInstance, computed } from 'vue'
import { marked } from 'marked'
import { baseUrl } from '../config'
import SelectComponent from '@/components/SelectComponent.vue';

const instance = getCurrentInstance()
const proxy = instance && instance.proxy
const startDialogueUrl = baseUrl + "/answer/start-dialogue";
const answerReviewUrl = baseUrl + "/answer/evaluate-response";

const aiLoading = ref(false);
const dialogue = ref({});
const message = ref("");
const userInput = ref("");
const inputDisabled = ref(true)

const renderMarkdownToHtml = computed(() => marked.parse(message.value))


async function fetchDialogue(chapterId) {
    aiLoading.value = true
    try {
        const res = await proxy.$axios.post(startDialogueUrl, { "chapter_id": chapterId })
        dialogue.value = res.data

        message.value = `🚀<b>Welcome</b>, ${dialogue.value.question}`
        aiLoading.value = false;
        inputDisabled.value = false;
    } catch(e) {
        console.log(`Error: ${e}`);        
    } finally {
        aiLoading.value = false;
        inputDisabled.value = false;
    }
    }
    
async function reviewAnswer() {
    // Display user response in UI
    dialogue.value["user_answer"] = userInput.value;
    message.value += `<b>Your Response</b><br> ${userInput.value} <br>`

    // prepare a plain JSON payload 
    const payload = { "answer": userInput.value, "session_id": dialogue.value.session_id }
    inputDisabled.value = true
    aiLoading.value = true

    try {
        const res = await proxy.$axios.post(answerReviewUrl, payload)
        console.log('Review response:', res.data)
        const evaluation = res.data
        message.value += `<b>AI</b> <br> ${evaluation["response"]}`

        if (evaluation.complete) {
            inputDisabled.value = true
            return
        }         
    } catch (error) {
        console.error('evaluate-response error:', error)
        if (error.response) {
            console.error('Status:', error.response.status, 'Data:', error.response.data)
            // show a concise message to the user (server validation details)
            message.value = `<span class="text-danger">Server: ${error.response.status} - ${JSON.stringify(error.response.data)}</span>`
        } else {
            message.value = `<span class="text-danger">Request failed</span>`
        }
    } finally {
        userInput.value = "";
        inputDisabled.value = false
        aiLoading.value = false
        window.scrollTo(0, document.body.scrollHeight)

    }
}

</script>

<style scoped>
#askInput {
    position: fixed;
    bottom: 10px;
    border: 1px solid rgb(20, 103, 220);
    max-width: 75vw;
}
#chapterSelect {
    min-width: 20vw;
}
</style>