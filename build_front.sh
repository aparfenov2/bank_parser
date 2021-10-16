npm run build
cp build/* public_prod
cp -r build/static .
#docker-compose build
#docker-compose push
