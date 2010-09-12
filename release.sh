#/bin/sh
LATEST=`git tag -l release-* | cut -b 9- | sort -n -r | head -n 1`
echo -n "Enter release to build [$LATEST]? "
read REL
if [ -z $REL ]; then
	REL="$LATEST"
fi

NAME="peex-$REL"
if [ -d $NAME ]; then
	echo -n "A directory called '$NAME' already exists. Remove? [N/y] "
	read CONFIRM
	if [ $CONFIRM != "y" ]; then
		echo "Release directory exists, aborting."
		exit 1
	fi
fi

echo "Building release '$NAME'"
rm -rf $NAME
mkdir -p $NAME
cp peex ops.py tree.py $NAME/
cp README example.peex $NAME/
tar -cf $NAME/$NAME.tar $NAME/
gzip $NAME/$NAME.tar

