#!/bin/bash

d=$(date +%Y-%m-%d)
git add .
git commit -m "$d"
git push origin master

cd lambda_receiver;rm configs.yaml
cd ..
cd lambda_start_stop;rm configs.yaml
cd ..
cp configs.yaml lambda_receiver
cp configs.yaml lambda_start_stop

rm lambda_receiver.zip
rm lambda_worker.zip
rm lambda_start_stop.zip

cd lambda_receiver; zip -r ../lambda_receiver.zip *
cd ..
cd lambda_worker; zip -r ../lambda_worker.zip *
cd ..
cd lambda_start_stop; zip -r ../lambda_start_stop.zip *
cd ..

terraform init
terraform plan
terraform apply

rm lambda_receiver.zip
rm lambda_worker.zip
rm lambda_start_stop.zip
