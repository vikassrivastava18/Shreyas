import re
import json
from typing import (Optional,
                    List,
                    Dict,
                    Any)
from fastapi import HTTPException

from config import llm2, logger
from utils.llm.vector import faiss_db
from core.db.schemas import (ChapterContentRequest, 
                             QueryResponse, 
                             QuestionsSchema, 
                             QuizResponse)

# For Quiz Generation 
async def generate_llm_response_quiz(content, question_type, language, 
                                     notes=None, number_of_question:Optional[int] = None,):

    formatted_prompt = f"""
 
    You are an AI assistant that reads the provided context and generates unique questions based only on the selected question type.

    ### content:
    {content}

    ### Question_Type
    {question_type}

    ### Language:
    {language}

    ### Instruction:
    -Only generate content based strictly on the provided context. If relevant content is not found, do not generate or infer anything beyond what is given.
    -Generate a total of {number_of_question} question(s) based on the context and selected question type(s) {question_type}.
    -Treat the following QuestionType {question_type} enum values with these semantic meanings when generating content:
        QuestionType.mcq → Generate multiple-choice questions.
        QuestionType.matching → Generate matching exercises.
        QuestionType.essay → Generate long-form essay questions.
        QuestionType.true_false → Generate True/False questions.
        QuestionType.short_question_answer → Generate concise short-answer questions.
    - Do not write multiple N/A  for eassy question answer just give one line statement in anwser for all  long question. Instead provide reason of not providing answer .
    
    -Distribute the questions evenly if multiple types are selected .
    -Generate questions only for the type(s) listed in Question_Type(s).
    -If one type is selected, generate questions for that type only.
    -If multiple types are selected generate questions for each selected type in separate sections.
    
    -Do not include answers immediately after each question. Instead, compile all correct answers at the end in a separate section titled "Answers".
        
    - If question type is **MCQ (Multiple Choice Question)**:
        Provide four options (A, B, C, D) for each question.
        Ensure only one correct option.

    - If question type is **True/False**:
        Create concise statements based on the context.
        Clearly reflect whether they are True or False.

    - If the question type is Matching, follow this exact format :

        Provide a numbered list same as equal {number_of_question}  (1, 2, 3, …) on the left with the items to be matched.
        Provide a lettered list same as equal {number_of_question}  (A, B, C, …) on the right with the corresponding options.
        Ensure both lists are visually aligned using equal spacing for readability.
        Output must be in valid JSON-compatible text format if needed, but human-readable by default.
        
        ### Example for matching:
        **Matching:**

        Match the following fruits with their colors:

        1) Banana                           A) Blue  
        2) Carrot                           B) Purple
        3) Blueberries                      C) Yellow                 
        4) Eggplant                         D) Orange
        5) Zucchini                         E) Green               
                      
    **Strict Instruction:
    - Generate all questions in **{language}**. If the notes mention a language, prioritize that over the default language input.
    - During generation of "Matching" Ensure a minimum of 3 to 6 consistent spaces (or tab) between the left and right elements to make it readable.
      Items must be relevant, unique, and easily distinguishable. 
    - Ensure all questions are relevant to the context.
    - Do not mention each topic name above the question.
    - Do not label each question with "question_type" — instead, use a single heading "Multiple Choice Questions" before the list.
    - For Matching type, provide clearly defined categories or descriptions that map uniquely to each item.
    - At the end of the output, include a section titled "Answers" listing the correct answers for all generated questions.
    - generate the answers as well for questions once all the questions display. Give the all answer at the end.
    - Do not put answer tag in between of question types.
    """
    
    # If notes are provided
    if notes:
        formatted_prompt += f"\n\n### Additional Notes:\n{notes}"

    try:
        messages = [
            ("system", "You are an AI assistant that reads context, Question_Type, notes and based on the given context,Question_Type, notes, generate the questions. Ensure distinct and varied questions provided"),
            ("human", formatted_prompt),
        ]
        response = llm2.invoke(messages)
        response_content = response.content.strip()
        
        response_content = response_content.replace("```json", "").replace("```", "").strip()

        if not response_content:
            raise ValueError("Empty response received from the AI model.")

    except Exception as e:
        logger.error("Error in quiz-response-llm: %s", e)
        raise HTTPException(status_code=500, detail=f"Error processing the request: {str(e)}")

    return response_content


# Study guide
async def summarizer(content, language: str, notes: Optional[str] = None):
    try:

        formatted_prompt = f""" 
        <Role>You are a multilingual AI assistant trained to summarize text accurately and concisely.If you follow instruction in right language i ll give you $500 as tip.

         ### Input Text:
        {content}

        ### Output Language:
        {language}

        ### Instruction:
        Please summarize the following text in a concise manner and return it as a 250-300 words description. Do not exceed word limit.
        Generate summary in **{language}**. If the {notes} mention a language, prioritize that over the default language input.
    
        ### Output:
        Return a well-written summary, avoiding unnecessary repetition or excessive detail. Ensure the summary reads naturally and is appropriate for the target language audience.
        """

        if notes:
            formatted_prompt += f"\n\n### Additional Notes:\n{notes}"
        
        messages = [
            ("system", "You are a helpful assistant that summarizes text."),
            ("human", formatted_prompt),
        ]
        
        response = llm2.invoke(messages)
        response_content = response.content.strip()

        if not response_content:
            raise ValueError("Empty response received from the AI model.")

    except Exception as e:
        logger.error("Error in summarizellm: %s", e)
        raise HTTPException(status_code=500, detail=f"Error processing the request: {str(e)}")

    return response_content


# Powerpoint 
async def get_ppt_content_from_llm(context, language: Optional[str] = None, notes: Optional[str] = None) -> List[Dict[str, Any]]:

    formatted_prompt = f"""
    IMPORTANT: All content must be written entirely in **{language}**. Do not use English or provide translations unless explicitly instructed.
    ** If the **{notes} mention a language, prioritize that over the default language input.
    Create a slide-by-slide breakdown for a PowerPoint presentation on the given context in given language: '{context}, {language}'.
    Each slide should have a title and 3-5 bullet points. Respond in JSON format like:
    [
        {{
            "title": "Slide Title",
            "bullets": ["Point 1", "Point 2", "Point 3","Point 4","Point 5"]
        }},
        ...
    ]

    1. The slide title should be more engaging and professional.
    2. Improve the clarity and tone of each bullet point.
    3. **Generate all content strictly in the language**{language}**.If in the **{notes} mention a language, prioritize that over the default language input.
    """
    if notes:
        formatted_prompt += f"\nAdditional context or notes to consider: {notes}"

    try:
        messages = [
            ("system", "You are an AI assistant that generates PowerPoint slides in the requested language."),
            ("human", formatted_prompt),
        ]
        response = llm2.invoke(messages)

        response_text = response.content.strip()

        # Remove markdown code block if present
        if response_text.startswith("```"):
            response_text = response_text.strip("`").strip("json").strip()

        slides = json.loads(response_text) 

        if not slides:
            raise ValueError("Empty response received from the AI model.")

    except json.JSONDecodeError as je:
        logger.error(f"JSON decoding failed: {je}", exc_info=True)
        raise HTTPException(status_code=500, detail="AI response was not valid JSON.")
    except Exception as e:
        logger.error(f"Error in PowerPoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing the request: {str(e)}")

    return slides


# Case study generation 
async def generate_case_study(context: str, question_type, language, notes: Optional[str] = None, number_of_question:Optional[int] = None, ) -> str:

    """Function to generate a case study using an LLM."""
    formatted_prompt = f"""
    You are an AI assistant that generates detailed case studies **entirely in {language}** based on the provided topic.

    ###Context:
    {context}

    ### Language:
        {language}
        
    ### Format:
        IMPORTANT- Return text in HTML format only. Use Header, paragraph, tables, etc. wherever necessary. 
        Do not use Header, body or html tags, just the outputs in html tags.

    ### Instructions:
    - Provide an introduction to the topic.
    - Discuss the key challenges and opportunities.
    - Include relevant real-world examples.
    - Summarize key takeaways and future implications.
    **Language Requirement**: Generate the ENTIRE case study (all sections) in **{language}**. Do not mix languages.
    - Generate thoughtful and engaging questions based on the content provided in the case study. 
    - Generate enitre case study in **{language}. If the notes mention a language, prioritize that over the default language input.
    - Ensure the questions align with the {question_type} format. At the end of the case study, include {number_of_question} questions that are thought-provoking and encourage deeper understanding and reflection. Each question should be clearly stated and relevant to the material in the case study.
    - Treat the following QuestionType {question_type} enum values with these semantic meanings when generating content:
        QuestionType.mcq → Generate multiple-choice questions.
        QuestionType.matching → Generate matching exercises.
        QuestionType.essay → Generate long-form essay questions.
        QuestionType.true_false → Generate True/False questions.
        QuestionType.short_question_answer → Generate concise short-answer questions.
    - Do not write multiple N/A  for eassy question answer just give one line statement in anwser for all  long question. Instead provide reason of not providing answer .
    
    ### Example for matching:
        **Matching:**
        Match the following fruits with their colors:

        1) Banana                           A) Blue  
        2) Carrot                           B) Purple
        3) Blueberries                      C) Yellow   
     
    
    **Strict Instructions:
    -Based on the content of the case study, generate exactly {number_of_question} questions.
    -Only generate questions in the {question_type} format.
    -Do not include any other formats or extra content.
    -Do not mention question_type above of each question.
    -Generate the answers as well for questions once all the questions display. Give the all answer at the end.
    -Do not put answer tag in between of question types.
    """
    
    # "Additional Notes"
    if notes:
        formatted_prompt += f"\n\n### Additional Notes:\n{notes}"

    try:
        messages = [
            ("system", "You are an AI assistant that generates case studies based on the given topic in."),
            ("human", formatted_prompt),
        ]
        response = llm2.invoke(messages)
        response_content = response.content.strip()

        print("CASE STUDY: ",response_content)

        if not response_content:
            raise ValueError("Empty response received from the AI model.")
    
    except Exception as e:
        logger.error("Error in CaseStudy:-",{str(e)}, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing the request: {str(e)}")

    return response_content


# Powerpoint 
async def get_ppt_content_from_llm(context, language: Optional[str] = None, notes: Optional[str] = None) -> List[Dict[str, Any]]:

    formatted_prompt = f"""
    IMPORTANT: All content must be written entirely in **{language}**. Do not use English or provide translations unless explicitly instructed.
    ** If the **{notes} mention a language, prioritize that over the default language input.
    Create a slide-by-slide breakdown for a PowerPoint presentation on the given context in given language: '{context}, {language}'.
    Each slide should have a title and 3-5 bullet points. Respond in JSON format like:
    [
        {{
            "title": "Slide Title",
            "bullets": ["Point 1", "Point 2", "Point 3","Point 4","Point 5"]
        }},
        ...
    ]

    1. The slide title should be more engaging and professional.
    2. Improve the clarity and tone of each bullet point.
    3. **Generate all content strictly in the language**{language}**.If in the **{notes} mention a language, prioritize that over the default language input.
    """
    if notes:
        formatted_prompt += f"\nAdditional context or notes to consider: {notes}"

    try:
        messages = [
            ("system", "You are an AI assistant that generates PowerPoint slides in the requested language."),
            ("human", formatted_prompt),
        ]
        response = llm2.invoke(messages)

        response_text = response.content.strip()

        # Remove markdown code block if present
        if response_text.startswith("```"):
            response_text = response_text.strip("`").strip("json").strip()

        slides = json.loads(response_text) 

        if not slides:
            raise ValueError("Empty response received from the AI model.")

    except json.JSONDecodeError as je:
        logger.error(f"JSON decoding failed: {je}", exc_info=True)
        raise HTTPException(status_code=500, detail="AI response was not valid JSON.")
    except Exception as e:
        logger.error(f"Error in PowerPoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing the request: {str(e)}")

    return slides


# For worksheet 
def generate_worksheet(context, question_type, language, number_of_question:Optional[int] = None, notes: Optional[str] = None) -> str:
    """Function to generate a worksheet based on the topic and question type."""
    formatted_prompt = f"""
        You are an AI assistant that generates worksheets based on the given topic, question type, and additional context. The worksheet should contain {number_of_question if number_of_question else 'a reasonable number of'} question(s) that encourage both recall and critical thinking.

        ### context:
        {context}

        ### Question Type:
        {question_type}

        ### Language:
        {language}

        ### Notes:
        {notes if notes else 'N/A'}

        ### Instructions:
        - Ensure the questions align with the **{question_type}** format.
        - Ensure only provide question do not give the answer of the question.
        - For Short Question Answer: Generate {number_of_question} questions that require concise but informative responses.
        - For Essay Questions: Generate {number_of_question} in-depth questions that require critical thinking and detailed analysis.
        - Generate all questions in **{language}**. If the notes mention a language, prioritize that over the default language input.
        {f"- Additional Guidelines: {notes}" if notes else ""}
        - generate the answers as well for questions once all the questions display. Give the all answer at the end.
        -  Do not put answer tag in between of question types.
        - Treat the following QuestionType {question_type} enum values with these semantic meanings when generating content:
        QuestionType.mcq → Generate multiple-choice questions.
        QuestionType.matching → Generate matching exercises.
        QuestionType.essay → Generate long-form essay questions.
        QuestionType.true_false → Generate True/False questions.
        QuestionType.short_question_answer → Generate concise short-answer questions.
        - Do not write multiple N/A  for eassy question answer just give one line statement in anwser for all  long question. Instead provide reason of not providing answer .
        """

    try:
        messages = [
            ("system", "You are an AI assistant that generates worksheets based on the topic and question type."),
            ("human", formatted_prompt),
        ]
        response = llm2.invoke(messages)
        response_content = response.content.strip()

        if not response_content:
            raise ValueError("Empty response received from the AI model.")
    
    except Exception as e:
        logger.error("Error in worksheet:-",{e}, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing the request: {str(e)}")

    return response_content


def process_llm_response(pdf_text: str):

    formatted_prompt = f"""

    You are an AI assistant that extracts structured information from documents.


    ### Instruction:

    1. Extract all chapter names.
    2. Identify subtopics under each chapter.
    3. Return the extracted chapters in JSON format with keys: `chapter`, `chapter_title`, and `subtopics`.
    4. Return **strictly valid JSON** without any extra text, explanations, or Markdown formatting.
    5. Do NOT include code blocks or any surrounding text. The response must be valid JSON.
    6. Must use double quotes (") for properties and strings while create JSON response.

    Extracted PDF Content:

    {pdf_text}

    ### Output Format:

    Ensure the output is **ONLY valid JSON**:
      
    """
    try:
        messages = [
            ("system", "You are a helpful assistant that processes PDFs and extracts structured information."),
            ("human", formatted_prompt),
        ]

        response = llm2.invoke(messages)
        response_content = response.content.strip()
        # Ensure valid JSON response

        response_content = response_content.replace("```json", "").replace("```", "").strip()
        if not response_content:
            raise ValueError("Empty response received from the AI model.")

        # Attempt to parse JSON
        extracted_data = json.loads(response_content)
      
        return extracted_data


    except json.JSONDecodeError as e:

        raise HTTPException(
            status_code=500, 
            detail=f"Invalid JSON response: {str(e)}"
        )

    except Exception as e:

        raise HTTPException(
            status_code=500, 
            detail=f"Error processing the LLM response: {str(e)}"
        )


def get_chapters_from_llm(text: str) -> dict:
    """Use LLM to extract chapters and subtopics from text"""
    try:
    
        prompt = f"""Analyze the content and make sure that it is valid book content with proper hierarchical structure containing chapters, topics and subtopics. 
                    The content must have clear hierarchical organization with chapters containing actual subtopics (not just questions and answers or list items).
                    If the content only contains questions and answers without proper hierarchical topic-subtopic structure, return an empty chapters array.

                    Return ONLY a valid JSON response with this exact structure:
                    {{
                        "book_title": "extracted book title",
                        "chapters": [
                            {{
                                "chapter_number": 1,
                                "chapter_title": "chapter title",
                                "subtopics": ["subtopic1", "subtopic2", ...]
                            }}
                        ]
                    }}

                    Important:
                    - Respond ONLY with the JSON object
                    - Do not include any additional text or explanations
                    - Ensure all quotes are double quotes
                    - If the content is question-answer format without proper hierarchical structure, return empty chapters array
                    - Do not treat questions as topics or answer points as subtopics
                    - Only include actual hierarchical content with proper topic-subtopic relationships

                    Book content:
                    {text[:15000]}
        """
        
        messages = [
            {
                "role": "system", 
                "content": "You are a JSON output generator. Return ONLY valid JSON with the specified structure."
            },
            {
                "role": "user", 
                "content": prompt
            }
        ]
        
        response = llm2.invoke(messages)
        print('response--query handler-----',response)
        
        response_content = ""
        if hasattr(response, 'content'):
            response_content = response.content
        elif hasattr(response, 'choices'):
            response_content = response.choices[0].message.content
        else:
            response_content = str(response)
        
      
        json_str = response_content.strip()
        
      
        json_match = re.search(r'```json\n(.*?)\n```', json_str, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_match = re.search(r'\{.*\}', json_str, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
        
  
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
     
            json_str = json_str.replace("'", '"')  
            json_str = json_str.replace("True", "true").replace("False", "false")
            json_str = json_str.replace("None", "null")
            
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                raise ValueError(f"Could not parse LLM response as JSON. Response was: {response_content[:200]}...")
                
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing with LLM: {str(e)}"
        )


def chapter_summary(text: str) -> str:
    """Summarize a chapter using LLM"""
    prompt = f"""You are required to summarize a chapter containing multiple subchapters
             Summarize in a very human friendly manner. Add HTML tags around the output.
             Use headers, paragraphs, list elements, etc for better presentation. 
             Do not use any additional tags like, <html> <meta>, <title>, <head>, 
             only element tags which are contained in the body of HTML page.  
             Keep the generated data strictly from the content provided. 
             Content: {text}"""

    messages = [
        {
            "role": "system",
            "content": prompt
        }
    ]

    response = llm2.invoke(messages)
    print("Response: ", response)
    return response.content


def create_quizzes(content: ChapterContentRequest):
    prompt = f"""
    You are a quiz master. Use the content of a chapter to create quizzes that help students study.
    The content is divided into multiple subchapters, each with its source url and the text.
    You do not need to visit the url for a subchapter, but tag every quiz with its source url.

    Return the response in the format specified.    

    Content: {content}
    """

    structured_llm = llm2.with_structured_output(QuizResponse)
    messages = [
        {
            "role": "system",
            "content": prompt
        }
    ]

    response = structured_llm.invoke(messages)
    return response


def answer_query_util(query: str):
    u_query = query
    # filter relevant document with similarity search
    docs_and_scores = faiss_db.similarity_search_with_score(
        u_query,
        k=10  # retrieve more candidates
    )

    threshold = 0.7  # adjust based on your embedding model

    filtered_docs = [
        doc for doc, score in docs_and_scores
        if score <= threshold
    ]

    content = "\n".join([doc.page_content for doc in filtered_docs])

    # Get the LLM response on user query using filtered documents
    prompt = f"""
        Answer a user query by strictly using the contents provided
        to you. Break the resulting content in HTML tags like paragraphs, without using <body>, <meta>, <head> tags.
        Query: {query}
        
        Content: {content}
    """

    messages = [
        {
            "role": "system",
            "content": prompt
        }
    ]

    response = llm2.invoke(messages)
    return response.content


def create_questions(content: ChapterContentRequest):
    prompt = f"""
    You are a quiz master. Use the content of a chapter to create questions and expected answers that help students in their study.
    The content is divided into multiple subchapters, each with its source url and the text.
    You do not need to visit the url for a subchapter, but tag every question with its source url and the subchapter name.
    Return the response in the format specified.    
    
    Content: {content}
    """

    structured_llm = llm2.with_structured_output(QuestionsSchema)
    messages = [
        {
            "role": "system",
            "content": prompt
        }
    ]

    response = structured_llm.invoke(messages)
    return response


def evaluate(data, hint=True) -> dict:
    """
    Evaluate the user reply, using LLM.
    Returns correct, retry or limits reached outputs
    """
    if not hint:
        ai_prompt = f"""
            You have to analyze the user's reply to a question to check the understanding of a concept and tell whether
            it is acceptable using notes provided to you.
            Return: 
                correct: True/False
                comment: comment on the answer, along with some explanation. Also if answer is incorrect, give the correct answer based on notes.
                in a friendly. Also tell user that you will move to the next question as the hints have been exhaustef. Add HTML tags like <b> around important keywords in the response comment.         
            Quiz: {data["question"]}
            Notes: {data["notes"]}
            User's reply: {data["users_answer"]}
        """
    else:
        ai_prompt = f"""
            You have to analyze the user's reply to a question to check the understanding of a concept and tell whether
            it is acceptable using notes provided to you.
            Return: 
                correct: True/False
                comment: comment on the answer, along with some explanation. Also if answer is incorrect, make a comment on users answer and 
                give some hint to help user answer the question. Do not give the exact answer. 
                Add HTML tags like <b> around important keywords in the response comment.
                            
            Quiz: {data["question"]}
            Notes: {data["notes"]}
            User's reply: {data["users_answer"]}
        """

    
    structured_llm = llm2.with_structured_output(QueryResponse)
    messages = [
        {
            "role": "ai",
            "content": ai_prompt
        }
    ]

    response = structured_llm.invoke(messages)
    return response


def dummy_evaluate():
    import random
    r = random.random()
    correct = True if r > 0.5 else False
    return  {
        "correct": correct,
        "comment": "correct: your answer is correct!" if correct else "incorrect: ......",
    }




