import requests

url = input("Please input website-url which is you want to check: ")
n = 0
print('')
for i in range(10):
    test_url = requests.post(url)
    if test_url.status_code == 200:
        n = n + 1
        print(f"This website is normal！(status_code: {test_url.status_code})")
    elif test_url.status_code == 302:
        print(f"Redirected on this website！(status_code: {test_url.status_code})")
    elif test_url.status_code == 403 or test_url.status_code == 404 or test_url.status_code == 400:
        print(f"Exceptions on this website！(status_code: {test_url.status_code})")
    else:
        print(f"Unknown response code！(status_code: {test_url.status_code})")
print('\nNormal Percent: {:.2f}%'.format(float(n*10)))
