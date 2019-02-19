# Config variables local to the script
version=${SOLR_VERSION}
file="solr-${version}.tgz"
url="http://mirror.reverse.net/pub/apache/lucene/solr/${version}/${file}"

# Make a downloads dir to cache and change working dir to it
mkdir -p downloads
cd downloads

# Check if the file exists for some reason, shouldn't but out of parsimony
if [ -f $file ];
then
        echo "File exists, skipping download..."
else
        wget $url
fi
# Untar
tar xzf $file

# Start the solr instance with all default settings
echo "Starting solr..."
bin="solr-${version}/bin/solr"
$bin start
if [ $? -eq 0 ];
then
        echo "Solr appears to have started..."
else
        exit 1
fi

echo "Solr running on default port of 8983..."
