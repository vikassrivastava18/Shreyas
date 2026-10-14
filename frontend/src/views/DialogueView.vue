<template>
    <div>
        <div class="container px-4 selectBox">
            <i class="py-4">
            <label for="askInput" class="control-label p-2 py-4">
                <b>Start a dialogue on any topic!</b>
            </label>
            </i>
            <SelectComponent @startDialogue="fetchDialogue" class="px-2" />
        </div>
        
        <div class="container">
            <div v-if="quizMode">
                <QuizComponent :quizzes="quizzes" @next-summary="nextTopic" />
                
            </div>
            <p v-else v-html="renderedMessage" class="p-4"></p>
            <div v-if="aiLoading" class="d-flex justify-content-center mt-4">
                <div class="spinner-grow text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            </div>
            <input class="form-control py-2 my-2" id="askInput" 
                v-model="userInput" placeholder="Enter your answer here..."
                @keyup.enter="sendResponse" :hidden="inputDisabled"
                v-if="!quizMode">            
        </div>
    </div>
</template>

<script setup>
import { ref, computed, getCurrentInstance } from 'vue'
import { marked } from 'marked'
import { baseUrl } from '../config'
import QuizComponent from '../components/QuizComponent.vue'
import SelectComponent from '@/components/SelectComponent.vue'

const instance = getCurrentInstance()
const proxy = instance && instance.proxy
const startDialogueUrl = baseUrl + "/dialogue/start-dialogue";
const answerReviewUrl = baseUrl + "/dialogue/review-response";
const nextTopicUrl = baseUrl + "/dialogue/next-topic";

const aiLoading = ref(false);
const dialogue = ref({});
const message = ref("");
const userInput = ref("");
const inputDisabled = ref(true)
const quizMode = ref(false)
const quizzes = ref({})

const renderedMessage = computed(() => marked.parse(message.value))


async function fetchDialogue(chapterId) {
    aiLoading.value = true
    const res = await proxy.$axios.post(startDialogueUrl,{"chapter_id": chapterId })    
    dialogue.value = res.data

    message.value = `🚀<b>Welcome</b>, we will be learning importance concepts related to the 
                    chapter.<br> <p>${dialogue.value.dialogue}</p>`
    aiLoading.value = false;
    inputDisabled.value = false;
}

async function sendResponse() {    
    message.value += "<br> <p>" + userInput.value + "</p>"
    const payload = { "answer": userInput.value, "session_id": dialogue.value.session_id }
    inputDisabled.value = true
    aiLoading.value = true

    try {
        const res = await proxy.$axios.post(answerReviewUrl, payload)
        const result = res.data.response
        if (res.data.state === "clear") {
            quizMode.value = true
            quizzes.value = result
        } else message.value = result

        window.scrollTo(0, document.body.scrollHeight)

    } catch (error) {
        console.error('evaluate-response error:', error)
        if (error.response) {
            // show a concise message to the user (server validation details)
            message.value = `<span class="text-danger">Server: ${error.response.status} 
                            - ${JSON.stringify(error.response.data)}</span>`
        } else {
            message.value = `<span class="text-danger">Request failed</span>`
        }
    } finally {
        aiLoading.value = false
        inputDisabled.value = false
    }
}

async function nextTopic() {
    inputDisabled.value = true
    aiLoading.value = true
    const payload = {"session_id": dialogue.value.session_id}
    try {
        const res = await proxy.$axios.post(nextTopicUrl, payload)
        
        const result = res.data.response
        quizMode.value = false
        message.value = result
        window.scrollTo(0, document.body.scrollHeight)

    } catch (error) {
        if (error.response) {
            // show a concise message to the user (server validation details)
            message.value = `<span class="text-danger">Server: ${error.response.status} 
                            - ${JSON.stringify(error.response.data)}</span>`
        } else {
            message.value = `<span class="text-danger">Request failed</span>`
        }
    } finally {
        aiLoading.value = false
        inputDisabled.value = false
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