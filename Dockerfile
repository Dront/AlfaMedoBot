FROM python:3.14-bookworm

RUN apt-get update; apt-get install -y --no-install-recommends ca-certificates make git zlib1g-dev libssl-dev gperf php-cli cmake clang libc++-dev libc++abi-dev;
RUN git clone --depth 1 https://github.com/tdlib/td.git; cd td; git checkout 5742c287cd514e7a1ee7908d63b4e5fca8638799
RUN mkdir -p td/build; cd td/build; CXXFLAGS="-stdlib=libc++" CC=/usr/bin/clang CXX=/usr/bin/clang++ cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX:PATH=../tdlib ..; cmake --build . --parallel 2 --target tdjson
ENV TD_LIBRARY_PATH="/td/build/libtdjson.so.1.8.59"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY get_clinics_list.py .
CMD ["python", "get_clinics_list.py"]
