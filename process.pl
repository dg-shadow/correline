while (<>)
{
    s/^\s+//;
    s/\s+/,/g;
    s/,$//;
    print;
    print "\n";
}
