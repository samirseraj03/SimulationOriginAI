from fastapi import FastAPI  , Request 
from fastapi.responses import HTMLResponse , JSONResponse 
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.encoders import jsonable_encoder


from starlette.requests import Request

import QueryDatabase
import tools

app = FastAPI()
# Path to serve static files like javascript and css
app.mount("/static", StaticFiles(directory="static"), name="static")
# to serve html templates
templates = Jinja2Templates(directory="templates")



# Route to serve the index.html
@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    # this is only test grafic
    data = QueryDatabase.get_data_simulations('SIM789')
    chart_data = tools.generate_chart(data)

    return templates.TemplateResponse(request=request, name="index.html", context={"chart_data": chart_data})


# api to get all data simulations
@app.get("/simulations", response_class=HTMLResponse)
async def get_simulations(request : Request):
    return await handle_request(lambda: QueryDatabase.get_simulations(), request)


# api to filter simulations indicating state  
@app.get("/simulations/{state}", response_class=HTMLResponse)
async def get_simulations( state: str , request : Request):
    return await handle_request(lambda: QueryDatabase.filter_simulations_bystat(state), request)


# api to order data simulations with name and start date
@app.get("/order", response_class=HTMLResponse)
async def order_simulations(request : Request):
    return await handle_request(lambda: QueryDatabase.OrderList(), request)


# api to search machine avaiable
@app.get("/machines/available", response_class=HTMLResponse)
async def get_machines_avaiable(request : Request):
    return await handle_request(lambda: QueryDatabase.get_machines_available(), request)


# api to post/create new simulation
#The list should appear like this:
# you need to use body to accept list
"""
    'simulation_id' : 'SAM105',
       'name' : 'For IA' ,
       'status' : 'Pending',
       'start_date' : today,
       'end_date' : today,
       'machine_id' : 'MACHINE_F'
"""
@app.post("/simulations", response_class=HTMLResponse)
async def create_simulations(request: Request):

    form_data = await request.form()  # Obtener datos del formulario
    list = {key: form_data.get(key) for key in form_data}
    return await handle_request(lambda: QueryDatabase.post_simulation(list), request)



# api to get detailed information of simulation specifying the id_simulation
@app.get("/simulations/detailed/{id_simulation}", response_class=HTMLResponse)
async def get_detailed_simulation(id_simulation: str , request : Request):
    return await handle_request(lambda: QueryDatabase.get_detailed_simulation(id_simulation), request)
 

# api to get grafic recoleting data  specifying the id_simulation
@app.get("/simulations/grafic/{id_simulation}", response_class=HTMLResponse)
async def get_grafic(id_simulation: str , request : Request):
    return await handle_request(lambda: tools.generate_chart(id_simulation), request) 


""" 
Function to check if the machine is working, 
if it is working, the frontend receives that the machine is working and obtains data for the graph in real time, 
when the machine is no longer working, it receives everything  
"""
@app.get("/simulations/data/{id_simulation}", response_class=HTMLResponse)
async def get_data_simulation(id_simulation: str , request : Request):

    try:
        # when the machine is running , we get latest data    
        data = QueryDatabase.get_data_simulations_realtime(id_simulation)  
        if not data or len(data) == 0:
            return templates.TemplateResponse(request=request, name="404.html", status_code=404)

        data = data[0]
        if data[7] == 'running':
            return JSONResponse(content=jsonable_encoder(data), status_code=200)
        else: 
            # When the state is no longer 'running', we get the full simulation data   
            data = QueryDatabase.get_data_simulations(id_simulation)
            if not data or len(data) == 0:
                 return templates.TemplateResponse(request=request, name="404.html", status_code=404)

            return JSONResponse(content=(data), status_code=200)

    except Exception as e:
        print(e)
        return templates.TemplateResponse(request=request, name="500.html", status_code=500)


#function to manage the request and return with a status
async def handle_request(query_func, request: Request):
    try:        
        data = query_func()
        if data:
            return JSONResponse(content=jsonable_encoder(data), status_code=200)
        else:
            return templates.TemplateResponse(request=request, name="404.html", status_code=404)
    except Exception as e:
        print(e)
        return templates.TemplateResponse(request=request, name="500.html", status_code=500)



# Run the application using uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
