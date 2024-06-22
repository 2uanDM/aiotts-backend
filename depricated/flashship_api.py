######################################
DEV_ENDPOINT = os.getenv("DEV_FLASHSHIP_ENDPOINT")
PROD_ENDPOINT = os.getenv("PROD_FLASHSHIP_ENDPOINT")


def get_flashship_header(auth: bool = False, access_token: str | None = None) -> dict:
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "vi,en-US;q=0.9,en;q=0.8,vi-VN;q=0.7",
        "access-control-allow-origin": "*",
        "origin": "https://devpod.flashship.net",
        "priority": "u=1, i",
        "referer": "https://devpod.flashship.net/upload-orders",
        "sec-ch-ua": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    }

    if auth:
        headers["authorization"] = f"Bearer {access_token}"

    return headers


##### login #####
class LoginBody(BaseModel):
    api_key: str
    username: str
    password: str


@app.post("/flashship/login", tags=["FlashShip"])
def login(body: LoginBody, mode: str = "dev"):
    api_key = body.api_key
    if not api_key or api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    if mode == "dev":
        endpoint = DEV_ENDPOINT
    elif mode == "prod":
        endpoint = PROD_ENDPOINT
    else:
        raise HTTPException(status_code=400, detail="Invalid mode")

    # Use the endpoint variable to construct the URL
    url = f"{endpoint}/seller-api-v2/token"

    print("==>> url:", url)

    try:
        response = requests.post(
            url=url,
            json={"username": body.username, "password": body.password},
            headers=get_flashship_header(),
        )
    except Exception as e:
        logger.error("Error while logging in:", exc_info=True)
        return JSONResponse(
            content={"msg": "fail", "error": str(e)},
            status_code=500,
        )

    status_code = response.status_code
    print(f"==>> login status_code: {status_code}")

    if response.json().get("msg") == "fail":
        status_code = 401

    return JSONResponse(
        content=response.json(),
        status_code=status_code,
    )


##### Create orders #####
class OrderBody(BaseModel):
    variant_id: int
    printer_design_front_url: str
    printer_design_back_url: str | None
    printer_design_right_url: str | None
    printer_design_left_url: str | None
    printer_design_neck_url: str | None
    mockup_front_url: None
    mockup_back_url: None
    mockup_right_url: None
    mockup_left_url: None
    mockup_neck_url: None
    quantity: int
    note: str


class OrderItem(BaseModel):
    access_token: str
    api_key: str
    order_id: str
    buyer_first_name: str
    buyer_last_name: str
    buyer_email: str
    buyer_phone: str
    buyer_address1: str
    buyer_address2: str
    buyer_city: str
    buyer_province_code: str
    buyer_zip: str
    buyer_country_code: str
    shipment: str
    link_label: str
    products: list[OrderBody]


@app.post("/flashship/order/create", tags=["FlashShip"])
def create_order(body: OrderItem, mode: str = "dev"):
    api_key = body.api_key
    if not api_key or api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    if mode == "dev":
        endpoint = DEV_ENDPOINT
    elif mode == "prod":
        endpoint = PROD_ENDPOINT
    else:
        raise HTTPException(status_code=400, detail="Invalid mode")

    # Use the endpoint variable to construct the URL
    url = f"{endpoint}/seller-api-v2/orders/shirt-add"
    print("==>> url:", url)

    try:
        response = requests.post(
            url=url,
            json=body.model_dump(),
            headers=get_flashship_header(auth=True, access_token=body.access_token),
        )
    except Exception as e:
        logger.error("Error while creating order:", exc_info=True)
        return JSONResponse(
            content={"msg": "fail", "error": str(e)},
            status_code=500,
        )

    status_code = response.status_code

    return JSONResponse(
        content=response.json(),
        status_code=status_code,
    )


##### Get orders details #####
@app.get("/flashship/order/details", tags=["FlashShip"])
def get_order_detail(
    api_key: str,
    access_token: str,
    order_code: str,
    mode: str = "dev",
):
    if not api_key or api_key != API_KEY:
        return HTTPException(status_code=401, detail="Invalid API key")

    if mode == "dev":
        endpoint = DEV_ENDPOINT
    else:
        endpoint = PROD_ENDPOINT

    url = f"{endpoint}/seller-api-v2/orders/{order_code}"

    print("==>> url:", url)

    try:
        response = requests.get(
            url=url,
            headers=get_flashship_header(auth=True, access_token=access_token),
        )
    except Exception as e:
        logger.error("Error while getting order details:", exc_info=True)
        return JSONResponse(
            content={"msg": "fail", "error": str(e)},
            status_code=500,
        )

    status_code = response.status_code

    return JSONResponse(
        content=response.json(),
        status_code=status_code,
    )


##### Cancel order #####
class CancelOrderBody(BaseModel):
    access_token: str
    api_key: str
    order_code_list: list[str]
    reject_note: str


@app.post("/flashship/order/cancel", tags=["FlashShip"])
def cancel_order(body: CancelOrderBody, mode: str = "dev"):
    api_key = body.api_key

    if not api_key or api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    if mode == "dev":
        endpoint = DEV_ENDPOINT
    else:
        endpoint = PROD_ENDPOINT

    url = f"{endpoint}/seller-api-v2/orders/seller-reject"

    try:
        response = requests.post(
            url=url,
            json=body.model_dump(),
            headers=get_flashship_header(auth=True, access_token=body.access_token),
        )
    except Exception as e:
        logger.error("Error while canceling order:", exc_info=True)
        return JSONResponse(
            content={"msg": "fail", "error": str(e)},
            status_code=500,
        )

    status_code = response.status_code

    return JSONResponse(
        content=response.json(),
        status_code=status_code,
    )
