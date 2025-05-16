import hashlib
import hmac
import datetime
import urllib.request
import urllib.parse
import sys
import os
import argparse

def sign(key, msg):
    """计算 HMAC-SHA256 签名"""
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

def getSignatureKey(key, dateStamp, regionName, serviceName):
    """生成签名密钥"""
    kDate = sign(('AWS4' + key).encode('utf-8'), dateStamp)
    kRegion = sign(kDate, regionName)
    kService = sign(kRegion, serviceName)
    kSigning = sign(kService, 'aws4_request')
    return kSigning

def download_s3_file(bucket_name, object_key, destination_path=None, host=None, port=None, region='us-east-1'):
    """
    从 S3/MinIO 下载文件，使用 AWS Signature Version 4
    
    参数:
        bucket_name (str): S3 存储桶名称
        object_key (str): 对象键（路径和文件名）
        destination_path (str): 本地保存路径，默认使用对象键中的文件名
        host (str): MinIO/S3 服务器主机名或 IP，如果未指定则使用 AWS S3
        port (str): MinIO/S3 服务器端口号，默认为 None（AWS S3 使用默认 HTTPS 端口）
        region (str): AWS 区域，默认为 us-east-1
    
    返回:
        bool: 下载成功返回 True，否则引发异常
    """
    # 从环境变量获取 AWS 凭证
    access_key = os.environ.get('AWS_ACCESS_KEY_ID')
    secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    
    # 验证必要的凭证是否存在
    if not access_key:
        raise ValueError("环境变量 AWS_ACCESS_KEY_ID 未设置")
    if not secret_key:
        raise ValueError("环境变量 AWS_SECRET_ACCESS_KEY 未设置")
    
    # 如果未指定下载路径，使用对象键的最后部分（文件名）
    if destination_path is None:
        destination_path = os.path.basename(object_key)
    
    # 当前时间（UTC）
    t = datetime.datetime.utcnow()
    amzdate = t.strftime('%Y%m%dT%H%M%SZ')  # ISO8601 格式
    datestamp = t.strftime('%Y%m%d')  # 日期格式 YYYYMMDD
    
    # ************* 第 1 步：构建请求 URL 和主机头 *************
    if host:
        # 使用自定义 MinIO 服务器
        if port:
            # 有指定端口
            host_header = f"{host}:{port}"
            endpoint = f"http://{host_header}/{bucket_name}/{object_key}"
        else:
            # 无指定端口，使用默认值
            host_header = host
            endpoint = f"http://{host}/{bucket_name}/{object_key}"
    else:
        # 使用 AWS S3
        host_header = f"{bucket_name}.s3.{region}.amazonaws.com"
        endpoint = f"https://{host_header}/{object_key}"
    
    # HTTP 请求方法
    method = 'GET'
    
    # 规范 URI（URI 路径编码）- 对象键需要 URL 编码
    if host:
        # MinIO 格式：/<bucket>/<object-key>
        canonical_uri = '/' + bucket_name + '/' + urllib.parse.quote(object_key)
    else:
        # AWS S3 格式：/<object-key>
        canonical_uri = '/' + urllib.parse.quote(object_key)
    
    # 规范查询字符串
    canonical_querystring = ''
    
    # 规范请求头
    canonical_headers = f'host:{host_header}\nx-amz-content-sha256:UNSIGNED-PAYLOAD\nx-amz-date:{amzdate}\n'
    
    # 签名所需的请求头
    signed_headers = 'host;x-amz-content-sha256;x-amz-date'
    
    # 创建负载哈希
    payload_hash = 'UNSIGNED-PAYLOAD'
    
    # 合并规范请求部分
    canonical_request = f"{method}\n{canonical_uri}\n{canonical_querystring}\n{canonical_headers}\n{signed_headers}\n{payload_hash}"
    
    # ************* 第 2 步：创建待签名字符串 *************
    algorithm = 'AWS4-HMAC-SHA256'
    credential_scope = f"{datestamp}/{region}/s3/aws4_request"
    string_to_sign = f"{algorithm}\n{amzdate}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
    
    # ************* 第 3 步：计算签名 *************
    signing_key = getSignatureKey(secret_key, datestamp, region, 's3')
    signature = hmac.new(signing_key, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()
    
    # ************* 第 4 步：创建授权头 *************
    authorization_header = (
        f"{algorithm} "
        f"Credential={access_key}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, "
        f"Signature={signature}"
    )
    
    # ************* 发送请求 *************
    headers = {
        'x-amz-date': amzdate,
        'x-amz-content-sha256': payload_hash,
        'Authorization': authorization_header
    }
    
    if host:
        print(f"正在从 MinIO 下载 http://{host_header}/{bucket_name}/{object_key} 到 {destination_path}...")
    else:
        print(f"正在从 AWS S3 下载 s3://{bucket_name}/{object_key} 到 {destination_path}...")
    
    req = urllib.request.Request(endpoint, headers=headers)
    
    try:
        with urllib.request.urlopen(req) as response:
            # 检查响应状态码
            if response.status == 200:
                # 写入文件
                with open(destination_path, 'wb') as f:
                    f.write(response.read())
                print(f"文件下载成功: {destination_path}")
                return True
            else:
                raise Exception(f"下载失败，状态码: {response.status}")
    except urllib.error.HTTPError as e:
        print(f"HTTP错误: {e.code} - {e.reason}")
        if e.code == 403:
            print("访问被拒绝，请检查您的凭证或存储桶权限")
        elif e.code == 404:
            print("文件或存储桶不存在")
        # 打印错误响应内容，帮助调试
        print(f"错误详情: {e.read().decode('utf-8')}")
        raise
    except Exception as e:
        print(f"下载过程中发生错误: {str(e)}")
        raise

def main():
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='从 S3 或 MinIO 下载文件')
    
    # 添加必需参数
    parser.add_argument('bucket', help='S3/MinIO 存储桶名称')
    parser.add_argument('object_key', help='对象路径和名称 (例如: path/to/file.txt)')
    
    # 添加可选参数
    parser.add_argument('-o', '--output', help='本地保存路径 (默认使用对象名称)')
    parser.add_argument('-s', '--server', help='MinIO 服务器地址 (例如: minio.example.com)')
    parser.add_argument('-p', '--port', help='MinIO 服务器端口 (例如: 9000)')
    parser.add_argument('-r', '--region', default='us-east-1', help='AWS 区域 (默认: us-east-1)')
    
    # 解析命令行参数
    args = parser.parse_args()
    
    try:
        download_s3_file(
            bucket_name=args.bucket,
            object_key=args.object_key,
            destination_path=args.output,
            host=args.server,
            port=args.port,
            region=args.region
        )
    except Exception as e:
        print(f"下载失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
