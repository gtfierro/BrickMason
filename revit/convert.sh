for file in xbos-dr-revit/*.txt; do
    python convert.py $file
done
mkdir xbos-dr-brick
mv xbos-dr-revit/*.ttl  xbos-dr-brick
