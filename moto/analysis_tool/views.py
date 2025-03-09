from django.shortcuts import render, redirect

def test(request):
    print("Test")
    return redirect("master_web")