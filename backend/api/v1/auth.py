import os

from dotenv import load_dotenv
from typing import Annotated
from pydantic import BaseModel

from fastapi import (APIRouter, Request, Form,
                     status, HTTPException, Depends)
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates

from config import logger, oauth2_scheme
from utils.common.common import create_access_token
from core.db.query import authenticate_user

auth_routes = APIRouter()
load_dotenv()

# Configure the template
templates = Jinja2Templates(directory="frontend")

class Token(BaseModel):
    access_token: str
    token_type: str


# TODO - MAJOR BUG!!
logged_in = False

def verify_login():
    """Dependency to verify login status"""
    if not logged_in:
        logger.warning("Unauthorized access attempt - user not logged in")
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/login?error=not_logged_in"}
        )


@auth_routes.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    logger.info("Login page accessed")
    return templates.TemplateResponse("login.html", {"request": request})


@auth_routes.post("/login/")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    global logged_in
    try:
        if username == os.getenv("user") and password == os.getenv("password"):
            logged_in = True
            logger.info(f"Successful login for user: {username}")
            return JSONResponse({"message": "Logged"})
        else:
            logger.warning(f"Failed login attempt with username: {username}")
            return RedirectResponse(url="/?error=invalid_credentials", status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        logger.error(f"Error during login process: {str(e)}", exc_info=True)
        return RedirectResponse(url="/?error=login_error", status_code=status.HTTP_303_SEE_OTHER)


@auth_routes.get("/logout")
async def logout():
    global logged_in
    logged_in = False
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@auth_routes.post("/token")
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
                                 ) -> Token:
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.username}
    )
    return Token(access_token=access_token, token_type="bearer")


@auth_routes.get("/me")
async def read_users_me(token: str = Depends(oauth2_scheme)):
    return {"token": token}