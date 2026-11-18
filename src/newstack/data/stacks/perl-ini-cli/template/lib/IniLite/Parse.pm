package IniLite::Parse;

use strict;
use warnings;

# Pure parsing: text in, a document hashref out. Nothing here reads a file,
# prints or exits, so every branch is a unit test.
#
# The document keeps source order, because an INI file that is rewritten in a
# different order is a diff nobody asked for:
#
#   {
#     order    => [ '', 'server', 'db' ],       # section names in file order
#     sections => { '' => { port => '80' }, ... },
#     keys     => { '' => [ 'port' ], ... },    # key order per section
#   }

my $UNNAMED = '';

sub new {
    my ($class) = @_;
    return bless {
        order    => [],
        sections => {},
        keys     => {},
    }, $class;
}

# Strips a trailing comment from an unquoted value. A '#' or ';' only starts a
# comment when it is the first non-space character or follows whitespace, so
# "pass#1" survives while "pass   # note" loses the note.
sub _strip_comment {
    my ($value) = @_;

    $value =~ s/\s+[;#].*\z//;
    return $value;
}

# Removes matching surrounding quotes and resolves backslash escapes inside.
sub _unquote {
    my ($value) = @_;

    if ($value =~ /\A(["'])(.*)\1\z/s) {
        my $body = $2;
        $body =~ s/\\n/\n/g;
        $body =~ s/\\t/\t/g;
        $body =~ s/\\\\(.)/$1/g;
        return $body;
    }

    return $value;
}

sub parse {
    my ($class, $text) = @_;
    $text = '' unless defined $text;

    my $self = $class->new();
    my $section = $UNNAMED;

    my $number = 0;
    for my $raw (split /\n/, $text, -1) {
        $number++;
        my $line = $raw;
        $line =~ s/\r\z//;

        next if $line =~ /\A\s*\z/;
        next if $line =~ /\A\s*[;#]/;

        if ($line =~ /\A\s*\[\s*([^\]]*?)\s*\]\s*(?:[;#].*)?\z/) {
            $section = $1;
            $self->_touch($section);
            next;
        }

        if ($line =~ /\A\s*([^=:]+?)\s*[=:]\s*(.*)\z/) {
            my ($key, $value) = ($1, $2);
            $value = _strip_comment($value);
            $value =~ s/\A\s+//;
            $value =~ s/\s+\z//;
            $value = _unquote($value);
            $self->_store($section, $key, $value);
            next;
        }

        die "line $number: expected [section] or key = value, got '$line'\n";
    }

    return $self;
}

# Registers a section the first time it is seen, so empty sections survive.
sub _touch {
    my ($self, $name) = @_;

    return if exists $self->{sections}{$name};

    push @{ $self->{order} }, $name;
    $self->{sections}{$name} = {};
    $self->{keys}{$name} = [];
    return;
}

sub _store {
    my ($self, $section, $key, $value) = @_;

    $self->_touch($section);
    push @{ $self->{keys}{$section} }, $key unless exists $self->{sections}{$section}{$key};
    $self->{sections}{$section}{$key} = $value;
    return;
}

sub order { return @{ $_[0]->{order} } }

sub has_section {
    my ($self, $name) = @_;
    return exists $self->{sections}{$name};
}

sub pairs {
    my ($self, $name) = @_;

    die "no such section: $name\n" unless $self->has_section($name);

    my $section = $self->{sections}{$name};
    return map { [ $_, $section->{$_} ] } @{ $self->{keys}{$name} };
}

sub get {
    my ($self, $name, $key) = @_;

    return undef unless $self->has_section($name);

    return $self->{sections}{$name}{$key};
}

# Resolves "section.key" (or just "key" for the unnamed section) into its value.
sub lookup {
    my ($self, $path) = @_;

    my ($section, $key) = $path =~ /\A(.*)\.([^.]+)\z/
        ? ($1, $2)
        : ($UNNAMED, $path);

    return ($self->get($section, $key), $section, $key);
}

# Flat { "section.key" => value } view, unnamed keys kept bare.
sub flatten {
    my ($self) = @_;

    my %flat;
    for my $name ($self->order) {
        for my $pair ($self->pairs($name)) {
            my ($key, $value) = @{$pair};
            $flat{ length $name ? "$name.$key" : $key } = $value;
        }
    }

    return \%flat;
}

1;
