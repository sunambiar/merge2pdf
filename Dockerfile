

FROM python:3.11-slim
#FROM python:3.11
WORKDIR /app

RUN apt-get update
RUN apt-get install -y python3 python3-pip

#RUN apt-get update && apt-get install -y \
#    libreoffice \
#    fonts-dejavu \
#    && rm -rf /var/lib/apt/lists/*
 
RUN apt-get install -y fonts-dejavu 
RUN apt-get install -y build-essential 
RUN apt-get install -y libssl-dev libffi-dev 
RUN apt-get install -y python-dev-is-python3
RUN apt-get install -y libreoffice

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production
ENV LOG_FILE=app.log
ENV TIME_LOG_FILE=conversion_time.log


#ADD fonts /usr/share/fonts/

#RUN /bin/sh -c soffice --headless


ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

EXPOSE 5000  5678
#EXPOSE map[5000/tcp:{}]

#CMD ["python", "-m", "debugpy", "--listen", "0.0.0.0:5678", "--wait-for-client", "app_Merge2PDFhtmlNew.py"]
#docker run -p 5000:5000 -p 5678:5678 merge2pdf:1.0

#CMD ["python", "app_Merge2PDFhtmlNew.py" ]
CMD ["python", "-X", "faulthandler", "-u", "app_Merge2PDFhtmlNew.py"]
#CMD ["python", "-X", "faulthandler", "-u", "app_Merge2PDFhtmlNew.py"]

# python merge2pdf.py --sheet MergerSheet  --output "../TempFinalMerged.pdf" "../TenderMergeFile.xlsx" "../Tender document Blade Servers CoverPages.docx"  "../Tender document Blade Servers NIT.docx" "../Tender document Blade Servers PriceBid.docx" "../Tender document Blade Servers TechnicalBid.docx" "../General Conditions of Contract-New.docx"

#CMD ["uvicorn", "api_appMerge2PDF:app", "--host", "0.0.0.0", "--port", "8000"]

########## Important Commands ####################

## Command to Build Image:
# docker build --no-cache -t merge2pdf:v1 .

## Command to Run Container:
# docker run --name test-container -p 5000:5000  merge2pdf:v1

## To enter inside a running container:
# docker exec -it <container-name> bash

## To view logs of any container
## docker logs <container-name>

## To list the containers
## docker ps -a

## To inspect an image:
# docker inspect <image-name>