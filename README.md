

## Installation guide

You will need to find a QT version whos ABI is close enough to the version of
Tableau Desktop you are using. This may be tricky, but lets trust the QT guys
for now.

I will document any version matchings for Tableau Desktop / QT version here so
you dont have to go through it.

- Tableau 10.1 : QT 5.6(seems to work...)


### Clean way: Using Nix

The easy way out is to use the [Nix]() package manager and use the provided `default.nix` file to grab everything. As this version does not pin down the Qt version, you may (but unlikely) have to work the version magic of nix and hydra.

### Less clean way: Using homebrew

For now, I'm assuming that you are trying this on a mac. Windows is currently untested.

#### Step 1. Grab QT

I used homebrew to get the proper version, there is a very nice and detailed
guide for ["How do I install a specific version of a formula in
homebrew?"](http://stackoverflow.com/a/4158763)


#### Step 2. Build the software

After installing QT, homebrew told me:

```
We agreed to the Qt opensource license for you.
If this is unacceptable you should uninstall.

This formula is keg-only, which means it was not symlinked into /usr/local.

Qt 5 has CMake issues when linked

Generally there are no consequences of this for you. If you build your
own software and it requires this formula, you'll need to add to your
build variables:

    LDFLAGS:  -L/usr/local/opt/qt5/lib
    CPPFLAGS: -I/usr/local/opt/qt5/include
    PKG_CONFIG_PATH: /usr/local/opt/qt5/lib/pkgconfig
```

So we need to add the proper QT location

```bash
# Create a build directory so we are nice and clean
mkdir _build && cd _build
# Generate the build
cmake . .. -DCMAKE_PREFIX_PATH=/usr/local/opt/qt5

# By default, command line Cmake creates unix makefiles,
# so we'll use just that
make
```

## Building on Windows

- You should install a version of Qt (for example 5.4 for most
  enterprise stuff) matching the target version of your target
  application via the Qt toolkit installer. This generally goes to
  `c:\Qt`

  After the install, CMake requires that you set `CMAKE_PREFIX_PATH` to
  point to your specific Qt version of the toolkit (like
  `C:/Qt/5.7/msvc2015_64`)


- Building requires `xxd` to be present.  If CMake cannot find it, set
  the `RESOURCE_COMPILER` cache variable to point to your installed
  `xxd` (for example `gVim` for Windows ships with a suitable `xxd.exe`)


- Use Visual Studio >= 2015 . Earlier versions lack support for some
  C++11/C++14 features used by `vaccine`


- To properly link the shared library generated by the project, you have
  to set the `CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS` cache variable to
  `TRUE`.


- IMPORTANT UNTIL FIXED: Always set Visual Studio to __LINK THE MSVC
  RUNTIME STATICALLY__ for the `qnject` target.

  (TODO: automate this in CMAKE if possible)



```cmd
cmake -DCMAKE_WINDOWS_EXPORT_ALL_SYMBOLS=TRUE -DCMAKE_PREFIX_PATH="C:\Qt\5.4\msvc2010_opengl" -DRESOURCE_COMPILER="C:\Program Files(x86)\Vim\vim74\xxd.exe"
```



### Injecting on Windows

The easiest way to inject the DLL into the running process in our
experience is to use [Injector by nefarius](https://github.com/nefarius/Injector).


```
Injector64.exe --process-name tableau.exe --module-name vaccine/Release/qnject.dll --inject
```





