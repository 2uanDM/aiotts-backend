from app.api.routes.google_sheet import GoogleSheetWorker

worker = GoogleSheetWorker("PHONGKD1-Designs-Files")
print(worker.read_sheet_data("PHONGKD1"))
