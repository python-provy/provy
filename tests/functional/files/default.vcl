backend nginx { 
  .host = "localhost";
  .port = "8888"; 
}

sub vcl_recv {
   set req.backend = nginx;
}

sub vcl_fetch {
    /* Remove Expires from backend, it's not long enough */
    unset beresp.http.expires;

    /* Set the clients TTL on this object */
    set beresp.http.cache-control = "max-age=86400";

    /* Set how long Varnish will keep it */
    set beresp.ttl = 1w;

    /* marker for vcl_deliver to reset Age: */
    set beresp.http.magicmarker = "1";
}

sub vcl_deliver {
    if (resp.http.magicmarker) {
        /* Remove the magic marker */
        unset resp.http.magicmarker;

        /* By definition we have a fresh object */
        set resp.http.age = "0";
    }
}
