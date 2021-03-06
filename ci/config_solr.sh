# Config variables local to the script
version=${SOLR_VERSION}
file="solr-${version}.tgz"
url="http://lib-solr-mirror.princeton.edu/dist/lucene/solr/${version}/${file}"

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

# copy in local configset in before starting
mkdir solr-${SOLR_VERSION}/server/solr/configsets/sandco
cp -r ../solr_conf/* solr-${SOLR_VERSION}/server/solr/configsets/sandco/

# Start the solr instance with all default settings
echo "Starting solr..."
bin="solr-${version}/bin/solr"
if $bin start
then
        echo "Solr appears to have started..."
else
        exit 1
fi

echo "Solr running on default port of 8983..."
