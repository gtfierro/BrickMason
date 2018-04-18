# Brick Mason
This is a little tool for building Brick models from a variety of data sources.

To generate a Brick model for a site, we need to write a `process.toml` file, which contains configuration information about the constructed model, and a set of drivers to configure and invoke in order to generate that model.

The `process.toml` file expects a main `[config]` section:

```toml
[config]
# XBOS namespace and filename
filename = "my-building-namespace"
# ontology URI to use for model
rdf_namespace = "http://xbos.io/ontologies/my-building-namespace"
# Turtle file containing extra classes we want to use
extra_classes = "extra_classes.ttl"
# output directory for brick models
output = "brick_models/"
```

* `filename`:  The value of this field will be used as the name of the generated Turtle file. In the above example, the generated Turtle file will be called `my-building-namespace.ttl`.
* `namespace`: Because a Brick model uses the RDF data model, we need a namespace to collect all of the building's entities. This is specified as a RDF-style URI.
* `output`: This is the output directory for the generated TTL file. If it does not exist, it will be created.

The `extra` section gets run last!

## Drivers

A driver is a Python file that contains a class called `Generator` whose constructor takes a reference to the current RDF graph (nominally called `G`) and a dictionary of configuration options (nominally called `cfg`). The constructor of the class uses RDFlib to add triples to the graph instance.

### Extra Triples: `mason.driver.ttlfile`

```toml
[extra]
    [extra.ttlfile]
    driver = "mason.driver.ttlfile"
    ttlfile = "extra_classes.ttl"
```

Configuration options:
- `ttlfile`: relative path to a Turtle file containing triples to be added to the graph

This driver is intended to be used if there is a pre-existing Brick model that needs to be augmented, or if there are triples containing extensions to Brick that have not yet been folded into the current release. This driver simply adds the triples contained in the specified Turtle file to the Brick graph.

### Site Attributes: `mason.driver.site`


```toml
[extra]
    [extra.siteattributes]
    driver = "mason.driver.site"
    human_name = "My Building"
    country = "US"
    zip_code = "123456"
    timezone = "America/Los_Angeles"
    square_feet = "7000"
    num_floors = "3"
    primary_function = "Small Commercial"
```

Configuration options:
- `human_name`: human-readable name for the site. Can be an arbitrary string rather than a URL-safe encoding (`brickframe:humanName`)
- `country`: country code for the site (`brickframe:country`)
- `zip_code`: zip code of the site (`brickframe:zipCode`)
- `timezone`: IANA timezone code for the site (`brickframe:timezone`)
- `square_feet`: the area of the building in sq ft (`brickframe:areaSquareFeet`)
- `square_meters`: the area of the building in sq meters (`brickframe:areaSquareMeters`)
- `num_floors`: the number of floors in the building (`brickframe:numFloors`)
- `primary_function`: the primary function of the building (e.g. "Apartment", "Butcher Shop", "Movie Theatre"). Right now this is an arbitrary string (`brickframe:primaryFunction`)

This adds the site object and all of its attributes to the model. This also adds the `bf:hasSite` edge to all objects in the model. For this reason, its considered good practice to put this driver in the `extra` section of the `process.toml` file so that it runs on the full Brick model.

### Revit Driver: `mason.driver.revit`

```toml
[revit]
    [revit.convert]
    driver = "mason.driver.revit"
    revit_schedule = "my-building-namespace.txt"
```

Configuration options:
- `revit_schedule`: relative path to an exported multi-schedule

This driver consumes the multi-schedule files that one can export from a Revit model of the building. TODO: get Greg to document what needs to happen here.

### IFC Driver: `mason.driver.ifc`

```toml
[ifc]
    [ifc.convert]
    driver = "mason.driver.ifc"
    ifc_file = "CIEE.ifc"
    ifc_schema = "IFC2X3_TC1.exp"
```

Configuration options:
- `ifc_file`: relative path to the IFC file to be used
- `ifc_schema`: relative path to the IFC schema file used to parse `ifc_file`

This extracts floors, HVAC zones and rooms from an IFC file and adds them to the Brick model.

### Haystack Driver: `mason.driver.haystack`

```toml
[haystack]
    [haystack.convert]
    driver = "mason.driver.haystack"
    siteref = 'sitename'
    ahu_filename = 'ahu.json'
    vav_filename = 'vav.json'
    points = 'points.csv'
```

Configuration options:
- `siteref`: which site to generate the Brick model for (sometimes Haystack exports can contain more than one site)
- `ahu_filename`: relative path to the JSON file containing exported points for all AHUs
- `vav_filename`: relative path to the JSON file containing exported points for all VAVs
- `points.csv`: full CSV dump of all points in the Haystack model

### XBOS Drivers

XBOS drivers require additional configuration which is placed in a special `config` section within the XBOS section. This configuration information is duplicated internally for each XBOS driver that is invoked.

**NOTE**: these drivers are highly dependent on the XBOS idioms that have been used in the XBOS-DR project

```toml
[xbos]
    [xbos.config]
    archiver = "ucberkeley"
    namespace = "my-building-namespace"
```

Configuration options:
- `archiver`: this is the base URI of the archiver used to find UUIDs for timeseries points
- `namespace`: this is the alias used to identify the site in BOSSWAVE

#### GreenButton Driver: `mason.driver.greenbutton`

```toml
[xbos]
    [xbos.config]
    # ...

    [xbos.GreenButton]
    driver  = "mason.driver.greenbutton"
    subid = 111111
    uuid = 1111111111
```

Configuration options:
- `subid`: the account number
- `uuid`: the meter identifier

This driver adds a Green Button meter which has been saved in the archiver to the Brick model. The `subid` and `uuid` fields are expected to be part of the URI.

#### NationalWeatherService Driver: `mason.driver.nationalweatherservice`

```toml
[xbos]
    [xbos.config]
    # ...

    [xbos.NationalWeatherService]
    driver = "mason.driver.nationalweatherservice"
    stations = [
        "AT565",
        "KTLC1",
    ]
```

Configuration options:
- `stations`: a list of string identifiers of the NWS stations to be associated with this site. This requires that the NWS stations have been added to the archiver

#### XBOS Interfaces Driver: `mason.driver.xbosinterfaces`

```toml
[xbos]
    [xbos.config]
    # ...

    [xbos.XBOSInterfaces]
    driver = "mason.driver.xbosinterfaces"
```

No configuration options.

This driver combs through the data streams archived for a namespace and inserts those devices into the Brick model along with their related points, URIs, UUIDs.
