import cv2
from ultralytics import YOLO
from azure.storage.blob import BlobServiceClient
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

STORAGE_ACCOUNT_NAME = os.getenv('STORAGE_ACCOUNT_NAME')
STORAGE_ACCOUNT_KEY = os.getenv('STORAGE_ACCOUNT_KEY')
CONTAINER_NAME = os.getenv('CONTAINER_NAME')

blob_service_client = BlobServiceClient(
    account_url=f"https://{STORAGE_ACCOUNT_NAME}.blob.core.windows.net",
    credential=STORAGE_ACCOUNT_KEY
)
container_client = blob_service_client.get_container_client(CONTAINER_NAME)

def upload_to_blob(file_path):
    blob_name = os.path.basename(file_path)
    blob_client = container_client.get_blob_client(blob_name)

    with open(file_path, "rb") as data:
        blob_client.upload_blob(data, overwrite=True)
    print(f"Arquivo {file_path} enviado para o blob.")

video = cv2.VideoCapture('accident-detector-dataset/ex01.mp4')
modelo = YOLO('yolov8n.pt')

area = [400, 100, 890, 360]
alarmeCtl = False
motos_em_area = []

output_video = None
video_writer = None
video_recording = False

while True:
    check, img = video.read()
    if not check:
        break

    img = cv2.resize(img, (1270, 720))
    img2 = img.copy()
    
    cv2.rectangle(img2, (area[0], area[1]), (area[2], area[3]), (0, 255, 0), 2)
    resultado = modelo(img)
    
    motos = []
    motos_atualizadas = []
    
    for objetos in resultado:
        obj = objetos.boxes
        for dados in obj:
            x1, y1, x2, y2 = map(int, dados.xyxy[0])
            cls = int(dados.cls[0])
            label = modelo.names[cls]
            
            cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 0), 2)
            cv2.putText(img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 2)
            
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            
            if cls == 3:
                motos.append((cx, cy, x1, y1, x2, y2))
                
                if cx >= area[0] and cx <= area[2] and cy >= area[1] and cy <= area[3]:
                    motos_atualizadas.append((cx, cy, x1, y1, x2, y2))
    
    colisao_detectada = False
    for i in range(len(motos)):
        for j in range(i + 1, len(motos)):
            cx1, cy1, x1_1, y1_1, x2_1, y2_1 = motos[i]
            cx2, cy2, x1_2, y1_2, x2_2, y2_2 = motos[j]
            
            if (x1_1 < x2_2 and x2_1 > x1_2 and y1_1 < y2_2 and y2_1 > y1_2):
                colisao_detectada = True
                break
        if colisao_detectada:
            break
    
    if colisao_detectada or len(motos_atualizadas) > 0:
        cv2.rectangle(img2, (area[0], area[1]), (area[2], area[3]), (0, 0, 255), -1)
        cv2.rectangle(img, (100, 30), (470, 80), (0, 0, 255), -1)
        cv2.putText(img, 'ACIDENTE DETECTADO', (105, 65), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 3)
        
        if not video_recording:
            data_e_hora = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            output_video = f'accidente_detectado_{data_e_hora}.mp4'
            fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
            video_writer = cv2.VideoWriter(output_video, fourcc, 20.0, (img.shape[1], img.shape[0]))
            video_recording = True
        
        if video_recording:
            video_writer.write(img)
    
    imgFinal = cv2.addWeighted(img2, 0.5, img, 0.5, 0)
    
    cv2.imshow('img', imgFinal)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

video.release()
cv2.destroyAllWindows()

if video_writer is not None:
    video_writer.release()
    upload_to_blob(output_video)  