<#
Download a curated set of Google Fonts into ./assets/fonts.

This script uses raw files from github.com/google/fonts. It only fetches open-license families.
If you're behind a proxy or GitHub blocks large downloads, adapt the URLs accordingly.

Run from project root (PowerShell):
  ./download_fonts.ps1
#>

$fonts = @(
    # Headline / display
    @{family='Montserrat'; files=@('Montserrat-Regular.ttf','Montserrat-Bold.ttf')},
    @{family='Poppins'; files=@('Poppins-Regular.ttf','Poppins-Bold.ttf')},
    @{family='Anton'; files=@('Anton-Regular.ttf')},
    @{family='AbrilFatface'; files=@('AbrilFatface-Regular.ttf')},
    @{family='Oswald'; files=@('Oswald-Regular.ttf','Oswald-Bold.ttf')},

    # Body / UI
    @{family='Roboto'; files=@('Roboto-Regular.ttf','Roboto-Bold.ttf')},
    @{family='OpenSans'; files=@('OpenSans-Regular.ttf','OpenSans-Bold.ttf')},
    @{family='Lato'; files=@('Lato-Regular.ttf','Lato-Bold.ttf')},
    @{family='SourceSansPro'; files=@('SourceSansPro-Regular.ttf','SourceSansPro-Bold.ttf')},
    @{family='Nunito'; files=@('Nunito-Regular.ttf','Nunito-Bold.ttf')},

    # Elegant Serif for premium look
    @{family='PlayfairDisplay'; files=@('PlayfairDisplay-Regular.ttf','PlayfairDisplay-Bold.ttf')},
    @{family='Merriweather'; files=@('Merriweather-Regular.ttf','Merriweather-Bold.ttf')},

    # Strong display prices
    @{family='ArchivoBlack'; files=@('ArchivoBlack-Regular.ttf')},
    @{family='BebasNeue'; files=@('BebasNeue-Regular.ttf')}
)

$outFolder = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) 'assets\fonts'
if(!(Test-Path $outFolder)) { New-Item -ItemType Directory -Path $outFolder | Out-Null }

Write-Host "Downloading fonts into $outFolder"

foreach($f in $fonts) {
    $family = $f.family
    foreach($fname in $f.files) {
        # Construct a raw GitHub URL to google/fonts. The exact path differs by family; we try common locations.
        $subPaths = @("main/ofl/$($family.ToLower())","main/apache/$($family.ToLower())","main/$($family.ToLower())")
        $success = $false
        foreach($sp in $subPaths) {
            $url = "https://raw.githubusercontent.com/google/fonts/$sp/$fname"
            $dest = Join-Path $outFolder $fname
            try {
                Write-Host "Trying $url"
                Invoke-WebRequest -Uri $url -UseBasicParsing -OutFile $dest -ErrorAction Stop
                Write-Host "Downloaded $fname"
                $success = $true
                break
            } catch {
                # try next
            }
        }
        if(-not $success) {
            Write-Warning "Could not download $fname for family $family. Check URL or add font manually."
        }
    }
}

Write-Host "Done. Please confirm the fonts exist in assets/fonts and restart the app if running."
