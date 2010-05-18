#/bin/sh
NAME=peex-1.0

echo "Building $NAME"
rm -rf $NAME
mkdir -p $NAME
cp peex defaults.peex ops.py tree.py $NAME/
cp README example.peex $NAME/
tar -cf $NAME.tar $NAME/
gzip $NAME.tar
